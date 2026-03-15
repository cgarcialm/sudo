import json
from unittest.mock import MagicMock

import anthropic
import pytest

from memory import (
    IDENTITY_MAX_CHARS,
    build_system_prompt,
    load_history,
    load_identity,
    reflect_and_update_identity,
    save_history,
    save_identity,
)


def test_load_history_returns_empty_when_missing(tmp_path):
    result = load_history(path=str(tmp_path / "history.json"))
    assert result == []


def test_load_history_returns_content(tmp_path):
    path = tmp_path / "history.json"
    data = [{"role": "user", "content": "hi"}]
    path.write_text(json.dumps(data))
    assert load_history(path=str(path)) == data


def test_save_history_creates_file(tmp_path):
    path = tmp_path / "sub" / "history.json"
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello"},
    ]
    save_history(history, path=str(path))
    assert path.exists()
    assert json.loads(path.read_text()) == history


def test_save_history_truncates_to_max_turns(tmp_path):
    path = tmp_path / "history.json"
    history = [{"role": "user", "content": str(i)} for i in range(100)]
    save_history(history, path=str(path), max_turns=10)
    saved = json.loads(path.read_text())
    assert len(saved) == 10
    assert saved[0]["content"] == "90"


def test_load_identity_returns_none_when_missing(tmp_path):
    result = load_identity(path=str(tmp_path / "identity.md"))
    assert result is None


def test_load_identity_returns_content(tmp_path):
    path = tmp_path / "identity.md"
    path.write_text("I am Sudo.")
    assert load_identity(path=str(path)) == "I am Sudo."


def test_save_identity_creates_file(tmp_path):
    path = tmp_path / "sub" / "identity.md"
    save_identity("I am Sudo.", path=str(path))
    assert path.exists()
    assert path.read_text() == "I am Sudo."


def test_build_system_prompt_without_identity():
    base = "You are Sudo."
    assert build_system_prompt(base) == base


def test_build_system_prompt_with_identity():
    base = "You are Sudo."
    identity = "I like robots."
    result = build_system_prompt(base, identity)
    assert base in result
    assert identity in result


def test_reflect_and_update_identity_saves_file(tmp_path):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="I am Sudo, a curious robot.")]
    )
    path = tmp_path / "identity.md"
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey"},
    ]

    result = reflect_and_update_identity(mock_client, history, path=str(path))

    assert path.exists()
    assert result == "I am Sudo, a curious robot."
    assert path.read_text() == "I am Sudo, a curious robot."


def test_reflect_and_update_identity_raises_on_api_error(tmp_path):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = anthropic.APIError(
        message="error", request=MagicMock(), body=None
    )
    with pytest.raises(RuntimeError, match="Claude API error during reflection"):
        reflect_and_update_identity(mock_client, [], path=str(tmp_path / "identity.md"))


def test_reflect_compresses_when_too_long(tmp_path):
    mock_client = MagicMock()
    long_text = "x" * (IDENTITY_MAX_CHARS + 1)
    mock_client.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text=long_text)]),  # reflection
        MagicMock(content=[MagicMock(text="compressed")]),  # compression
    ]
    path = tmp_path / "identity.md"

    reflect_and_update_identity(mock_client, [], path=str(path))

    assert path.read_text() == "compressed"
