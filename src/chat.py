import dataclasses
import logging
import os
import pathlib
import queue
import re
import sys
import threading
import time
from datetime import datetime
from typing import Callable

import anthropic

from config import (
    EXPRESSION_HISTORY_WINDOW,
    EXPRESSION_INTERVAL_SECONDS,
    GALLERY_DIR,
    GALLERY_ENABLED,
    MAX_HISTORY_TURNS,
    MAX_TOKENS_CHAT,
    MAX_TOKENS_EXPRESSION,
    MODEL,
    SCREEN_PNG_PATH,
)
from memory import (
    append_note,
    build_system_prompt,
    load_history,
    load_identity,
    load_notes,
    load_summaries,
    reflect_and_update_identity,
    save_history,
)
import prompts
from screen import ScreenRenderer

log = logging.getLogger("sudo")

_MODEL = MODEL
_MAX_TOKENS = MAX_TOKENS_CHAT


@dataclasses.dataclass
class ToolDef:
    name: str
    description: str
    handler: Callable[[str], None] | None = None
    main_thread: bool = False
    returns_result: bool = False


TOOLS: dict[str, ToolDef] = {
    "screen": ToolDef(
        name="screen",
        description=(
            "Render SVG on your physical 480×320 screen. "
            "Embed a complete SVG sized 480x320 (landscape) inside the tag. "
            "You decide whether to draw — it is your screen."
        ),
        main_thread=True,
    ),
    "remember": ToolDef(
        name="remember",
        description=(
            "Write a note you want to keep across sessions. "
            "Anything — an idea, something you noticed, a question. "
            "Your voice, your choice."
        ),
    ),
}


def _build_tool_descriptions(tools: dict[str, ToolDef]) -> str:
    lines = [f"- <{name}>...</{name}>: {t.description}" for name, t in tools.items()]
    return "You have these output channels:\n" + "\n".join(lines)


SYSTEM_PROMPT = prompts.BASE + "\n\n" + _build_tool_descriptions(TOOLS)


def _first_tool_tag_pos(buffer: str, tool_names, start: int = 0) -> int:
    """Return position of the earliest tool tag opener in buffer, or -1."""
    positions = [
        p for name in tool_names if (p := buffer.find(f"<{name}>", start)) != -1
    ]
    return min(positions) if positions else -1


def parse_reply(raw: str, tool_names) -> tuple[str, dict[str, str | None]]:
    """Extract text and tool calls from a raw reply.

    Returns (text, calls) where calls maps tool name → content string (or None
    if the tag was present but empty).
    """
    calls: dict[str, str | None] = {}
    text = raw
    for name in tool_names:
        m = re.compile(rf"<{name}>(.*?)</{name}>", re.DOTALL).search(text)
        if m:
            calls[name] = m.group(1).strip() or None
            text = (text[: m.start()] + text[m.end() :]).strip()
    return text.strip(), calls


@dataclasses.dataclass
class ScreenState:
    svg: str | None = None
    lock: threading.Lock = dataclasses.field(default_factory=threading.Lock)

    def get_svg(self) -> str | None:
        with self.lock:
            return self.svg

    def set_svg(self, svg: str) -> None:
        with self.lock:
            self.svg = svg


def build_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def send_message(client, history, user_message, system_prompt=SYSTEM_PROMPT):
    """Send a message to Claude and return (text, calls).

    Mutates history in place: appends the user message before the call
    and the parsed text (without tool tags) after.
    """
    history.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            messages=history,
        )
        raw = response.content[0].text
        text, calls = parse_reply(raw, TOOLS.keys())
        history.append({"role": "assistant", "content": text})
        return text, calls
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e


def _stream_reply(client, history, user_message, system_prompt, tools):
    """Stream a reply to stdout, suppressing any tool tag blocks.

    Prints text as it arrives. Stops printing once any tool tag is detected.
    Mutates history in place. Returns (text, calls).
    """
    tool_names = list(tools.keys())
    max_tag_len = max(len(f"<{name}>") for name in tool_names)

    history.append({"role": "user", "content": user_message})
    buffer = ""
    printed = 0
    tag_found = False

    print("\n> Sudo: ", end="", flush=True)
    try:
        with client.messages.stream(
            model=_MODEL,
            max_tokens=_MAX_TOKENS,
            system=system_prompt,
            messages=history,
        ) as stream:
            for chunk in stream.text_stream:
                buffer += chunk
                if not tag_found:
                    pos = _first_tool_tag_pos(buffer, tool_names, printed)
                    if pos != -1:
                        sys.stdout.write(buffer[printed:pos])
                        sys.stdout.flush()
                        tag_found = True
                    else:
                        safe = len(buffer) - max_tag_len + 1
                        if safe > printed:
                            sys.stdout.write(buffer[printed:safe])
                            sys.stdout.flush()
                            printed = safe
        if not tag_found and printed < len(buffer):
            sys.stdout.write(buffer[printed:])
            sys.stdout.flush()
        print()
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e

    text, calls = parse_reply(buffer, tool_names)
    history.append({"role": "assistant", "content": text})
    del history[: max(0, len(history) - MAX_HISTORY_TURNS)]
    return text, calls


def _dispatch_tool_calls(calls, action_queue, tools):
    """Route tool calls: main-thread tools go on the queue, others run inline."""
    for name, content in calls.items():
        if content is None:
            continue
        tool = tools[name]
        if tool.main_thread:
            action_queue.put((tool, content))
        else:
            tool.handler(content)


def _expression_loop(client, action_queue, tools, system_prompt, history, screen_state):
    """Background thread: periodically invite Sudo to express itself.

    Main-thread tool results (e.g. screen renders) go on action_queue.
    """
    tool_names = list(tools.keys())
    while True:
        time.sleep(EXPRESSION_INTERVAL_SECONDS)
        log.debug("expression loop firing (history=%d turns)", len(history))
        try:
            snapshot = history[-EXPRESSION_HISTORY_WINDOW:]
            effective_system = _system_with_screen(system_prompt, screen_state)
            messages = snapshot + [{"role": "user", "content": prompts.EXPRESSION}]
            response = client.messages.create(
                model=_MODEL,
                max_tokens=MAX_TOKENS_EXPRESSION,
                system=effective_system,
                messages=messages,
            )
            raw = response.content[0].text.strip()
            log.debug("expression loop got reply (len=%d): %.80s", len(raw), raw)
            if raw:
                _, calls = parse_reply(raw, tool_names)
                if calls:
                    log.debug("expression loop dispatching tool calls: %s", list(calls))
                    _dispatch_tool_calls(calls, action_queue, tools)
                else:
                    log.debug("expression loop: reply had no tool calls")
            else:
                log.debug("expression loop: empty reply (Sudo chose not to act)")
        except Exception as e:
            log.error("expression loop error: %s", e)


def _save_to_gallery(svg):
    now = datetime.now()
    path = pathlib.Path(GALLERY_DIR) / now.strftime("%Y-%m-%d/%H-%M-%S.svg")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(svg)
    log.debug("gallery saved %s", path)


def _render_and_save(renderer, svg, screen_state):
    log.debug("rendering SVG (%d bytes)", len(svg))
    renderer.render(svg)
    renderer.save(SCREEN_PNG_PATH)
    screen_state.set_svg(svg)
    if GALLERY_ENABLED:
        _save_to_gallery(svg)


def _system_with_screen(system_prompt, screen_state):
    """Append current screen SVG to system prompt if set."""
    svg = screen_state.get_svg()
    if not svg:
        return system_prompt
    return system_prompt + f"\n\nYour screen is currently showing:\n{svg}"


def _setup_logging():
    logging.basicConfig(
        format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stderr,
    )
    log.setLevel(os.environ.get("LOG_LEVEL", "WARNING"))


def _make_tools(renderer, screen_state, client):
    """Create the tool registry with live handlers bound to runtime state."""

    def _handle_screen(content: str) -> None:
        _render_and_save(renderer, content, screen_state)

    def _handle_remember(content: str) -> None:
        append_note(client, content)

    return {
        "screen": dataclasses.replace(TOOLS["screen"], handler=_handle_screen),
        "remember": dataclasses.replace(TOOLS["remember"], handler=_handle_remember),
    }


def run_chat():
    _setup_logging()
    client = build_client()
    history = load_history()
    identity = load_identity()
    notes = load_notes()
    summaries = load_summaries()
    system_prompt = build_system_prompt(SYSTEM_PROMPT, identity, notes, summaries)
    screen_state = ScreenState()
    renderer = ScreenRenderer()
    tools = _make_tools(renderer, screen_state, client)
    action_queue = queue.Queue()
    threading.Thread(
        target=_expression_loop,
        args=(client, action_queue, tools, system_prompt, history, screen_state),
        daemon=True,
    ).start()

    input_queue = queue.Queue()

    def _read_input():
        while True:
            try:
                line = input()
                input_queue.put(line)
            except (EOFError, KeyboardInterrupt):
                input_queue.put(None)
                return

    def _prompt():
        sys.stdout.write("> ")
        sys.stdout.flush()

    threading.Thread(target=_read_input, daemon=True).start()
    print("Sudo is ready. Type 'exit' to quit.\n")
    _prompt()

    while True:
        renderer.tick()
        try:
            tool, content = action_queue.get_nowait()
            tool.handler(content)
        except queue.Empty:
            pass
        try:
            user_input = input_queue.get(timeout=0.05)
        except queue.Empty:
            continue
        if user_input is None:
            print("\nGoodbye.\n")
            break
        user_input = user_input.strip()
        if not user_input:
            _prompt()
            continue
        if user_input.lower() == "exit":
            print("Goodbye.\n")
            break
        effective_system = _system_with_screen(system_prompt, screen_state)
        text, calls = _stream_reply(
            client, history, user_input, effective_system, tools
        )
        _dispatch_tool_calls(calls, action_queue, tools)
        _prompt()

    renderer.stop()
    save_history(history)
    try:
        print("Saving memories...", end="", flush=True)
        reflect_and_update_identity(client, history)
        print(" done.")
    except RuntimeError as e:
        print(f"\nWarning: could not update identity: {e}")


if __name__ == "__main__":
    run_chat()
    # Force exit: daemon threads (input reader, expression loop) can block
    # Python's cleanup of sys.stdin, causing a hang after "done.".
    os._exit(0)
