import os
from unittest.mock import MagicMock, patch

import anthropic
import pytest

from chat import send_message


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_returns_reply(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello, I'm Sudo!")]
    )

    history = []
    reply = send_message(mock_client, history, "Hello")

    assert reply == "Hello, I'm Sudo!"


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
    # history list is mutated in place, so check the third message was the user turn
    assert messages_sent[2] == {"role": "user", "content": "Second message"}


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
