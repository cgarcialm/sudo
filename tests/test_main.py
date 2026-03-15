import os
from unittest.mock import MagicMock, patch

import pytest

from main import ask_claude


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("main.anthropic.Anthropic")
def test_ask_claude_returns_response(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello!")]
    )

    result = ask_claude("Say hi")

    assert result == "Hello!"


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("main.anthropic.Anthropic")
def test_ask_claude_sends_prompt(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello!")]
    )

    ask_claude("Say hi")

    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs["messages"]
    assert messages[0]["content"] == "Say hi"


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("main.anthropic.Anthropic")
def test_ask_claude_raises_on_api_error(mock_anthropic):
    import anthropic

    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.side_effect = anthropic.APIError(
        message="error", request=MagicMock(), body=None
    )

    with pytest.raises(RuntimeError, match="Claude API error"):
        ask_claude("Say hi")
