import os
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from chat import SYSTEM_PROMPT, parse_reply, send_message


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_returns_reply(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello, I'm Sudo!")]
    )

    history = []
    text, grid = send_message(mock_client, history, "Hello")

    assert text == "Hello, I'm Sudo!"
    assert grid is None


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_appends_to_history(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hi!")]
    )

    history = []
    send_message(mock_client, history, "Hello")

    assert len(history) == 2
    assert history[0] == {"role": "user", "content": "Hello"}
    assert history[1] == {"role": "assistant", "content": "Hi!"}


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_passes_full_history(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Sure!")]
    )

    history = [
        {"role": "user", "content": "First message"},
        {"role": "assistant", "content": "First reply"},
    ]
    send_message(mock_client, history, "Second message")

    call_args = mock_client.messages.create.call_args
    messages_sent = call_args.kwargs["messages"]
    assert messages_sent[2] == {"role": "user", "content": "Second message"}


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_passes_system_prompt(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hi!")]
    )

    send_message(mock_client, [], "Hello")

    call_args = mock_client.messages.create.call_args
    assert call_args.kwargs["system"] == SYSTEM_PROMPT


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_raises_on_api_error(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.side_effect = anthropic.APIError(
        message="error", request=MagicMock(), body=None
    )

    with pytest.raises(RuntimeError, match="Claude API error"):
        send_message(mock_client, [], "Hello")


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_strips_screen_from_history(mock_anthropic):
    """Screen data is not stored in history — only the text reply."""
    grid_json = str([["#000000"] * 16 for _ in range(16)])
    raw = f"<screen>{grid_json}</screen>\nHello!"
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text=raw)])

    history = []
    send_message(mock_client, history, "Hi")

    assert history[1]["content"] == "Hello!"


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_returns_grid_when_present(mock_anthropic):
    import json

    grid = [["#ff0000"] * 16 for _ in range(16)]
    raw = f"<screen>{json.dumps(grid)}</screen>\nRed screen."
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text=raw)])

    history = []
    text, returned_grid = send_message(mock_client, history, "Hi")

    assert text == "Red screen."
    assert returned_grid == grid


def test_parse_reply_returns_text_and_none_when_no_screen_tag():
    text, grid = parse_reply("Hello there!")
    assert text == "Hello there!"
    assert grid is None


def test_parse_reply_extracts_grid_and_strips_screen_tag():
    import json

    grid = [["#abcdef"] * 16 for _ in range(16)]
    raw = f"<screen>{json.dumps(grid)}</screen>\nSome reply."
    text, returned_grid = parse_reply(raw)
    assert text == "Some reply."
    assert returned_grid == grid


def test_parse_reply_when_invalid_json_in_screen_tag():
    raw = "<screen>not valid json</screen>\nHello."
    text, grid = parse_reply(raw)
    assert text == "Hello."
    assert grid is None


def test_parse_reply_trims_whitespace():
    raw = "  Plain reply with spaces.  "
    text, grid = parse_reply(raw)
    assert text == "Plain reply with spaces."
    assert grid is None
