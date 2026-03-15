import json
from unittest.mock import MagicMock

import anthropic
import pytest

from memory import (
    IDENTITY_MAX_CHARS,
    build_system_prompt,
    load_history,
    load_identity,
    load_summaries,
    reflect_and_update_identity,
    save_history,
    save_identity,
    save_summary,
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


def test_load_identity_returns_content(tmp_path):
    path = tmp_path / "identity.md"
    path.write_text("I am Sudo.")
    assert load_identity(path=str(path)) == "I am Sudo."


def test_load_identity_returns_none_when_missing(tmp_path):
    assert load_identity(path=str(tmp_path / "identity.md")) is None


def test_save_identity_creates_file(tmp_path):
    path = tmp_path / "sub" / "identity.md"
    save_identity("I am Sudo.", path=str(path))
    assert path.exists()
    assert path.read_text() == "I am Sudo."


def test_load_summaries_returns_empty_when_missing(tmp_path):
    assert load_summaries(path=str(tmp_path / "summaries.json")) == []


def test_load_summaries_returns_content(tmp_path):
    path = tmp_path / "summaries.json"
    path.write_text(json.dumps(["session one", "session two"]))
    assert load_summaries(path=str(path)) == ["session one", "session two"]


def test_save_summary_appends(tmp_path):
    path = tmp_path / "summaries.json"
    save_summary("first", path=str(path))
    save_summary("second", path=str(path))
    assert load_summaries(path=str(path)) == ["first", "second"]


def test_save_summary_trims_to_max(tmp_path):
    path = tmp_path / "summaries.json"
    for i in range(12):
        save_summary(f"session {i}", path=str(path), max_summaries=10)
    result = load_summaries(path=str(path))
    assert len(result) == 10
    assert result[0] == "session 2"
    assert result[-1] == "session 11"


def test_build_system_prompt_base_only():
    assert build_system_prompt("You are Sudo.") == "You are Sudo."


def test_build_system_prompt_with_identity():
    result = build_system_prompt("You are Sudo.", identity="I like robots.")
    assert "You are Sudo." in result
    assert "I like robots." in result


def test_build_system_prompt_with_summaries():
    result = build_system_prompt("base", summaries=["session 1", "session 2"])
    assert "session 1" in result
    assert "session 2" in result


def test_build_system_prompt_with_all():
    result = build_system_prompt(
        "base", identity="identity text", summaries=["s1", "s2"]
    )
    assert "base" in result
    assert "identity text" in result
    assert "s1" in result
    assert "s2" in result


def test_reflect_and_update_identity_saves_file(tmp_path):
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = [
        MagicMock(content=[MagicMock(text="I am Sudo, a curious robot.")]),  # identity
        MagicMock(content=[MagicMock(text="We talked about robots.")]),  # summary
    ]
    path = tmp_path / "identity.md"
    summaries_path = tmp_path / "summaries.json"
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey"},
    ]

    result = reflect_and_update_identity(
        mock_client, history, path=str(path), summaries_path=str(summaries_path)
    )

    assert path.exists()
    assert result == "I am Sudo, a curious robot."
    assert path.read_text() == "I am Sudo, a curious robot."
    assert load_summaries(path=str(summaries_path)) == ["We talked about robots."]


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

    # Parallel execution: reflect/summarize arrive in non-deterministic order.
    # Dispatch by message content so the mock is order-independent.
    def fake_create(*args, **kwargs):
        content = kwargs.get("messages", [{}])[-1].get("content", "")
        if "Rewrite your identity" in content:
            return MagicMock(content=[MagicMock(text=long_text)])
        elif "Write a short summary" in content:
            return MagicMock(content=[MagicMock(text="summary text")])
        else:  # compress
            return MagicMock(content=[MagicMock(text="compressed")])

    mock_client.messages.create.side_effect = fake_create
    path = tmp_path / "identity.md"
    summaries_path = tmp_path / "summaries.json"

    reflect_and_update_identity(
        mock_client, [], path=str(path), summaries_path=str(summaries_path)
    )

    assert path.read_text() == "compressed"
