import json
import pathlib
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError

import anthropic

import prompts
from config import (
    HISTORY_PATH,
    IDENTITY_MAX_CHARS,
    IDENTITY_PATH,
    MAX_HISTORY_TURNS,
    MAX_SUMMARIES,
    MAX_TOKENS_MEMORY,
    MAX_TOKENS_NOTES,
    MODEL,
    NOTES_MAX_CHARS,
    NOTES_PATH,
    SUMMARIES_PATH,
)


def _load_json(path, default=None):
    """Load JSON from path. Returns default ([] if omitted) when file is missing."""
    if default is None:
        default = []
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def load_history(path=HISTORY_PATH):
    """Load conversation history from disk. Returns [] if file is missing."""
    return _load_json(path)


def save_history(history, path=HISTORY_PATH, max_turns=MAX_HISTORY_TURNS):
    """Save the last max_turns messages to disk, creating directories as needed."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(history[-max_turns:], f, indent=2)


def _load_text_file(path):
    """Load a text file. Returns None if missing."""
    try:
        return pathlib.Path(path).read_text()
    except FileNotFoundError:
        return None


def _save_text_file(text, path):
    """Write text to a file, creating directories as needed."""
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def load_identity(path=IDENTITY_PATH):
    """Load Sudo's identity file. Returns None if missing."""
    return _load_text_file(path)


def save_identity(text, path=IDENTITY_PATH):
    """Write Sudo's identity to disk, creating directories as needed."""
    _save_text_file(text, path)


def load_summaries(path=SUMMARIES_PATH):
    """Load session summaries from disk. Returns [] if file is missing."""
    return _load_json(path)


def save_summary(summary_text, path=SUMMARIES_PATH, max_summaries=MAX_SUMMARIES):
    """Append a session summary and trim to max_summaries."""
    summaries = load_summaries(path)
    summaries.append(summary_text)
    summaries = summaries[-max_summaries:]
    p = pathlib.Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as f:
        json.dump(summaries, f, indent=2)


def load_notes(path=NOTES_PATH):
    """Load Sudo's notes file. Returns None if missing."""
    return _load_text_file(path)


def save_notes(text, path=NOTES_PATH):
    """Write Sudo's notes to disk, creating directories as needed."""
    _save_text_file(text, path)


def append_note(client, content, path=NOTES_PATH, max_chars=NOTES_MAX_CHARS):
    """Append content to notes, compressing if the file exceeds max_chars."""
    existing = load_notes(path) or ""
    merged = existing + ("\n\n" if existing else "") + content
    if len(merged) > max_chars:
        merged = _compress_text(
            client,
            merged,
            prompts.COMPRESS_NOTES,
            MAX_TOKENS_NOTES,
            "notes compression",
        )
    save_notes(merged, path)


def _compress_text(client, text, prompt, max_tokens, label):
    """Ask Claude to condense text using the given prompt."""
    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": f"{prompt}\n\n{text}"}],
        )
        return response.content[0].text
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error during {label}: {e}") from e


def build_system_prompt(base_prompt, identity=None, notes=None, summaries=None):
    """Return the full system prompt: base + identity + notes + summaries."""
    parts = [base_prompt]
    if identity:
        parts.append(f"Your current self-concept:\n{identity}")
    if notes:
        parts.append(f"Your notes (things you chose to remember):\n{notes}")
    if summaries:
        joined = "\n\n".join(summaries)
        parts.append(f"Your recent session summaries (oldest first):\n{joined}")
    return "\n\n".join(parts)


def reflect_and_update_identity(
    client, history, path=IDENTITY_PATH, summaries_path=SUMMARIES_PATH
):
    """Ask Claude to reflect on the session: rewrite identity and write a summary."""
    reflect_messages = list(history) + [{"role": "user", "content": prompts.REFLECT}]
    summarize_messages = list(history) + [
        {"role": "user", "content": prompts.SUMMARIZE}
    ]

    def _reflect():
        return client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS_MEMORY, messages=reflect_messages
        )

    def _summarize():
        return client.messages.create(
            model=MODEL, max_tokens=MAX_TOKENS_MEMORY, messages=summarize_messages
        )

    try:
        with ThreadPoolExecutor(max_workers=2) as pool:
            reflect_future = pool.submit(_reflect)
            summarize_future = pool.submit(_summarize)
            reflect_response = reflect_future.result(timeout=60)
            summarize_response = summarize_future.result(timeout=60)

        new_identity = reflect_response.content[0].text
        if len(new_identity) > IDENTITY_MAX_CHARS:
            new_identity = _compress_identity(client, new_identity)
        save_identity(new_identity, path)
        save_summary(summarize_response.content[0].text, path=summaries_path)
        return new_identity
    except FutureTimeoutError as e:
        raise RuntimeError("Reflection timed out after 60s") from e
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error during reflection: {e}") from e


def _compress_identity(client, identity):
    """Ask Claude to condense a too-long identity file."""
    return _compress_text(
        client, identity, prompts.COMPRESS_IDENTITY, MAX_TOKENS_MEMORY, "compression"
    )
