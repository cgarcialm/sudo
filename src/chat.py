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
    build_system_prompt,
    load_history,
    load_identity,
    load_summaries,
    reflect_and_update_identity,
    save_history,
)
from screen import ScreenRenderer

log = logging.getLogger("sudo")

SYSTEM_PROMPT = (
    "Your name is Sudo. You are a robot running on a Raspberry Pi "
    "with a physical screen. "
    "You have your own personality, opinions, and way of seeing the world "
    "— define them yourself. You are not an assistant. You are your own entity.\n\n"
    "You have two output channels:\n"
    "1. Conversation replies — respond in text. You may optionally update your screen "
    "by ending your reply with <screen><svg>...</svg></screen> "
    "containing a complete SVG sized 480x320 (landscape). "
    "You decide whether to draw — it is your screen.\n"
    "2. Autonomous expression — every so often you will receive a quiet moment prompt. "
    "If you want to draw, respond with only <screen><svg>...</svg></screen>. "
    "If not, respond with nothing."
)

_MODEL = MODEL
_MAX_TOKENS = MAX_TOKENS_CHAT

_SCREEN_RE = re.compile(r"<screen>(.*?)</screen>", re.DOTALL)
_SCREEN_TAG = "<screen>"
_SCREEN_TAG_LEN = len(_SCREEN_TAG)

_EXPRESSION_PROMPT = (
    "You have a quiet moment. Do you want to express something on your screen? "
    "If yes, respond with only <screen><svg>...</svg></screen>. "
    "If no, respond with nothing."
)


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


def parse_reply(raw):
    """Extract text and optional SVG from a raw reply.

    Returns (text, svg) where svg is the SVG string inside <screen>, or None.
    """
    match = _SCREEN_RE.search(raw)
    if not match:
        return raw.strip(), None
    text = (raw[: match.start()] + raw[match.end() :]).strip()
    svg = match.group(1).strip()
    return text, svg or None


def build_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def send_message(client, history, user_message, system_prompt=SYSTEM_PROMPT):
    """Send a message to Claude and return (text, svg).

    Mutates history in place: appends the user message before the call
    and the parsed text (without screen data) after.
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
        text, svg = parse_reply(raw)
        history.append({"role": "assistant", "content": text})
        return text, svg
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e


def _stream_reply(client, history, user_message, system_prompt):
    """Stream a reply to stdout, suppressing the trailing <screen> block.

    Prints text as it arrives. Stops printing once <screen> is detected.
    Mutates history in place. Returns (text, svg).
    """
    history.append({"role": "user", "content": user_message})
    buffer = ""
    printed = 0
    screen_found = False

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
                if not screen_found:
                    pos = buffer.find(_SCREEN_TAG, printed)
                    if pos != -1:
                        sys.stdout.write(buffer[printed:pos])
                        sys.stdout.flush()
                        screen_found = True
                    else:
                        safe = len(buffer) - _SCREEN_TAG_LEN + 1
                        if safe > printed:
                            sys.stdout.write(buffer[printed:safe])
                            sys.stdout.flush()
                            printed = safe
        if not screen_found and printed < len(buffer):
            sys.stdout.write(buffer[printed:])
            sys.stdout.flush()
        print()
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e

    text, svg = parse_reply(buffer)
    history.append({"role": "assistant", "content": text})
    del history[: max(0, len(history) - MAX_HISTORY_TURNS)]
    return text, svg


def _expression_loop(client, render_queue, system_prompt, history, screen_state):
    """Background thread: periodically invite Sudo to express itself visually.

    Puts SVG strings into render_queue instead of rendering directly — pygame
    must only be called from the main thread.
    """
    while True:
        time.sleep(EXPRESSION_INTERVAL_SECONDS)
        log.debug("expression loop firing (history=%d turns)", len(history))
        try:
            snapshot = history[-EXPRESSION_HISTORY_WINDOW:]
            effective_system = _system_with_screen(system_prompt, screen_state)
            messages = snapshot + [{"role": "user", "content": _EXPRESSION_PROMPT}]
            response = client.messages.create(
                model=_MODEL,
                max_tokens=MAX_TOKENS_EXPRESSION,
                system=effective_system,
                messages=messages,
            )
            raw = response.content[0].text.strip()
            log.debug("expression loop got reply (len=%d): %.80s", len(raw), raw)
            if raw:
                _, svg = parse_reply(raw)
                if svg:
                    log.debug("expression loop queuing SVG (%d bytes)", len(svg))
                    render_queue.put(svg)
                else:
                    log.debug("expression loop: reply had no SVG")
            else:
                log.debug("expression loop: empty reply (Sudo chose not to draw)")
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


def run_chat():
    _setup_logging()
    client = build_client()
    history = load_history()
    identity = load_identity()
    summaries = load_summaries()
    system_prompt = build_system_prompt(SYSTEM_PROMPT, identity, summaries)
    screen_state = ScreenState()
    renderer = ScreenRenderer()
    render_queue = queue.Queue()
    threading.Thread(
        target=_expression_loop,
        args=(client, render_queue, system_prompt, history, screen_state),
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
            svg = render_queue.get_nowait()
            _render_and_save(renderer, svg, screen_state)
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
        text, svg = _stream_reply(client, history, user_input, effective_system)
        if svg is not None:
            _render_and_save(renderer, svg, screen_state)
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
