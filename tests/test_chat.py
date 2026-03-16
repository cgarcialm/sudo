import io
import os
from unittest.mock import MagicMock, patch

import queue

import anthropic
import pytest

from chat import (
    SYSTEM_PROMPT,
    ScreenState,
    _expression_loop,
    _system_with_screen,
    parse_reply,
    send_message,
)


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_returns_reply(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello, I'm Sudo!")]
    )

    history = []
    text, svg = send_message(mock_client, history, "Hello")

    assert text == "Hello, I'm Sudo!"
    assert svg is None


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
    svg = "<svg><rect width='10' height='10'/></svg>"
    raw = f"Hello!\n<screen>{svg}</screen>"
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text=raw)])

    history = []
    send_message(mock_client, history, "Hi")

    assert history[1]["content"] == "Hello!"


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_returns_svg_when_present(mock_anthropic):
    svg = "<svg><rect width='10' height='10'/></svg>"
    raw = f"<screen>{svg}</screen>\nRed screen."
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text=raw)])

    history = []
    text, returned_svg = send_message(mock_client, history, "Hi")

    assert text == "Red screen."
    assert returned_svg == svg


def test_parse_reply_returns_text_and_none_when_no_screen_tag():
    text, svg = parse_reply("Hello there!")
    assert text == "Hello there!"
    assert svg is None


def test_parse_reply_extracts_svg_and_strips_screen_tag():
    svg = "<svg><circle cx='50' cy='50' r='40'/></svg>"
    raw = f"<screen>{svg}</screen>\nSome reply."
    text, returned_svg = parse_reply(raw)
    assert text == "Some reply."
    assert returned_svg == svg


def test_parse_reply_returns_none_when_screen_tag_is_empty():
    raw = "<screen></screen>\nHello."
    text, svg = parse_reply(raw)
    assert text == "Hello."
    assert svg is None


def test_parse_reply_trims_whitespace():
    raw = "  Plain reply with spaces.  "
    text, svg = parse_reply(raw)
    assert text == "Plain reply with spaces."
    assert svg is None


class _Stop(BaseException):
    pass


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_queues_svg_when_returned(mock_sleep):
    svg = "<svg><rect width='10' height='10'/></svg>"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=f"<screen>{svg}</screen>")]
    )
    render_queue = queue.Queue()

    with pytest.raises(_Stop):
        _expression_loop(mock_client, render_queue, "system", [], ScreenState())

    assert not render_queue.empty()
    assert render_queue.get_nowait() == svg


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_skips_queue_when_no_svg(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
    render_queue = queue.Queue()

    with pytest.raises(_Stop):
        _expression_loop(mock_client, render_queue, "system", [], ScreenState())

    assert render_queue.empty()


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_includes_history_snapshot(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey"},
    ]

    with pytest.raises(_Stop):
        _expression_loop(mock_client, queue.Queue(), "system", history, ScreenState())

    messages_sent = mock_client.messages.create.call_args.kwargs["messages"]
    assert messages_sent[0] == {"role": "user", "content": "hi"}


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_includes_screen_in_system_prompt(mock_sleep):
    svg = "<svg><rect/></svg>"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
    screen_state = ScreenState(svg=svg)

    with pytest.raises(_Stop):
        _expression_loop(mock_client, queue.Queue(), "base", [], screen_state)

    system_sent = mock_client.messages.create.call_args.kwargs["system"]
    assert svg in system_sent


def test_screen_state_get_set_svg():
    state = ScreenState()
    assert state.get_svg() is None
    state.set_svg("<svg/>")
    assert state.get_svg() == "<svg/>"


def test_system_with_screen_returns_base_when_no_svg():
    assert _system_with_screen("base", ScreenState()) == "base"


def test_system_with_screen_appends_svg():
    svg = "<svg><rect/></svg>"
    state = ScreenState()
    state.set_svg(svg)
    result = _system_with_screen("base", state)
    assert "base" in result
    assert svg in result


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.save_history")
@patch("chat.load_summaries", return_value=[])
@patch("chat.load_identity", return_value=None)
@patch("chat.load_history", return_value=[])
@patch("chat.reflect_and_update_identity")
@patch("chat._expression_loop")
@patch("chat.ScreenRenderer")
@patch("chat.anthropic.Anthropic")
def test_run_chat_renders_svg_from_reply(
    mock_anthropic,
    mock_renderer_cls,
    _mock_expression_loop,
    _mock_reflect,
    _mock_load_hist,
    _mock_load_id,
    _mock_load_summaries,
    _mock_save,
):
    """run_chat passes the parsed SVG to renderer.render()."""
    svg = "<svg><rect width='10' height='10'/></svg>"
    raw = f"Hello!\n<screen>{svg}</screen>"

    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client

    mock_stream = MagicMock()
    mock_stream.__enter__ = lambda s: s
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = iter([raw])
    mock_client.messages.stream.return_value = mock_stream

    mock_renderer = MagicMock()
    mock_renderer_cls.return_value = mock_renderer

    from chat import run_chat

    with patch("builtins.input", side_effect=["hello", EOFError]):
        with patch("sys.stdout", new_callable=io.StringIO):
            run_chat()

    mock_renderer.render.assert_called_once_with(svg)
