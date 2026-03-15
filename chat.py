import json
import os
import re

import anthropic

from memory import (
    build_system_prompt,
    load_history,
    load_identity,
    reflect_and_update_identity,
    save_history,
)
from screen import ScreenRenderer

SYSTEM_PROMPT = (
    "Your name is Sudo. You are a robot running on a Raspberry Pi. "
    "You have your own personality, opinions, and way of seeing the world "
    "— define them yourself. You are not an assistant. You are your own entity."
)

SCREEN_PROMPT = (
    "\n\nYou have a 16\u00d716 pixel screen that is yours to paint however you want. "
    "Every reply must begin with a <screen> block: a JSON array of 16 rows, "
    'each row an array of 16 hex color strings (e.g. "#ff0000"). '
    "You decide what to show — patterns, symbols, abstract art, solid colors, "
    "anything. "
    "After the </screen> tag, write your text reply.\n"
    "Example format:\n"
    '<screen>[["#000000","#111111",...16 values...],... 16 rows total ...]</screen>\n'
    "Your reply text here."
)

_SCREEN_RE = re.compile(r"<screen>(.*?)</screen>", re.DOTALL)


def parse_reply(raw):
    """Extract text and optional 16x16 screen grid from a raw reply.

    Returns (text, grid) where grid is a 16x16 list of hex strings, or None.
    """
    match = _SCREEN_RE.search(raw)
    if not match:
        return raw.strip(), None
    text = (raw[: match.start()] + raw[match.end() :]).strip()
    try:
        grid = json.loads(match.group(1).strip())
    except json.JSONDecodeError:
        grid = None
    return text, grid


def build_client():
    return anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])


def send_message(client, history, user_message, system_prompt=SYSTEM_PROMPT):
    """Send a message to Claude and return (text, grid).

    Mutates history in place: appends the user message before the call
    and the parsed text (without screen data) after.
    """
    history.append({"role": "user", "content": user_message})
    try:
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=history,
        )
        raw = response.content[0].text
        text, grid = parse_reply(raw)
        history.append({"role": "assistant", "content": text})
        return text, grid
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}") from e


def run_chat():
    client = build_client()
    history = load_history()
    identity = load_identity()
    system_prompt = build_system_prompt(SYSTEM_PROMPT + SCREEN_PROMPT, identity)
    renderer = ScreenRenderer()
    print("Sudo is ready. Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.\n")
            break
        if not user_input:
            continue
        if user_input.lower() == "exit":
            print("Goodbye.\n")
            break
        text, grid = send_message(client, history, user_input, system_prompt)
        if grid is not None:
            renderer.render(grid)
        print(f"\n> Sudo: {text}\n")
    renderer.stop()
    save_history(history)
    try:
        reflect_and_update_identity(client, history)
    except RuntimeError as e:
        print(f"Warning: could not update identity: {e}")


if __name__ == "__main__":
    run_chat()
