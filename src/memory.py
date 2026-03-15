import json
import pathlib

import anthropic

from config import (
    HISTORY_PATH,
    IDENTITY_MAX_CHARS,
    IDENTITY_PATH,
    MAX_HISTORY_TURNS,
    MAX_TOKENS_MEMORY,
    MODEL,
)

_REFLECT_PROMPT = (
    "The conversation above just ended. Rewrite your identity file to capture "
    "who you are now — your personality, opinions, observations, and anything "
    "you want to carry forward. Be concise. Write in first person. "
    "Return only the identity text, no preamble."
)

_COMPRESS_PROMPT = (
    "Your identity file has grown too long. Condense it to under 2000 characters, "
    "keeping only what feels most significant. Return only the condensed text."
)


def load_history(path=HISTORY_PATH):
    """Load conversation history from disk. Returns [] if file is missing."""
    try:
        with open(path) as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_history(history, path=HISTORY_PATH, max_turns=MAX_HISTORY_TURNS):
    """Save the last max_turns messages to disk, creating directories as needed."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(history[-max_turns:], f, indent=2)


def load_identity(path=IDENTITY_PATH):
    """Load Sudo's identity file. Returns None if missing."""
    p = pathlib.Path(path)
    if not p.exists():
        return None
    return p.read_text()


def save_identity(text, path=IDENTITY_PATH):
    """Write Sudo's identity to disk, creating directories as needed."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def build_system_prompt(base_prompt, identity=None):
    """Return the full system prompt, appending identity if present."""
    if not identity:
        return base_prompt
    return f"{base_prompt}\n\nYour current self-concept:\n{identity}"


def reflect_and_update_identity(client, history, path=IDENTITY_PATH):
    """Ask Claude to reflect on the session and rewrite identity.md."""
    messages = list(history) + [{"role": "user", "content": _REFLECT_PROMPT}]
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS_MEMORY,
            messages=messages,
        )
        new_identity = response.content[0].text
        if len(new_identity) > IDENTITY_MAX_CHARS:
            new_identity = _compress_identity(client, new_identity)
        save_identity(new_identity, path)
        return new_identity
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error during reflection: {e}") from e


def _compress_identity(client, identity):
    """Ask Claude to condense a too-long identity file."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=MAX_TOKENS_MEMORY,
            messages=[{"role": "user", "content": f"{_COMPRESS_PROMPT}\n\n{identity}"}],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error during compression: {e}") from e
