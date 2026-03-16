import io
import os
from unittest.mock import MagicMock, patch

import queue

import anthropic
import pytest

from chat import (
    SYSTEM_PROMPT,
    ScreenState,
    _dispatch_tool_calls,
    _expression_loop,
    _first_tool_tag_pos,
    _make_tools,
    _save_to_gallery,
    _system_with_screen,
    parse_reply,
    send_message,
)

# ---------------------------------------------------------------------------
# parse_reply
# ---------------------------------------------------------------------------


def test_parse_reply_returns_text_and_empty_dict_when_no_tags():
    text, calls = parse_reply("Hello there!", ["screen", "remember"])
    assert text == "Hello there!"
    assert calls == {}


def test_parse_reply_extracts_screen_and_strips_tag():
    svg = "<svg><circle cx='50' cy='50' r='40'/></svg>"
    raw = f"<screen>{svg}</screen>\nSome reply."
    text, calls = parse_reply(raw, ["screen", "remember"])
    assert text == "Some reply."
    assert calls["screen"] == svg


def test_parse_reply_returns_none_when_screen_tag_is_empty():
    raw = "<screen></screen>\nHello."
    text, calls = parse_reply(raw, ["screen"])
    assert text == "Hello."
    assert calls["screen"] is None


def test_parse_reply_trims_whitespace():
    text, calls = parse_reply("  Plain reply with spaces.  ", ["screen"])
    assert text == "Plain reply with spaces."
    assert calls == {}


def test_parse_reply_extracts_remember():
    raw = "Hello!<remember>A curious thought.</remember>"
    text, calls = parse_reply(raw, ["screen", "remember"])
    assert text == "Hello!"
    assert calls["remember"] == "A curious thought."


def test_parse_reply_extracts_multiple_tools():
    svg = "<svg/>"
    raw = f"Hi!<screen>{svg}</screen><remember>noted</remember>"
    text, calls = parse_reply(raw, ["screen", "remember"])
    assert text == "Hi!"
    assert calls["screen"] == svg
    assert calls["remember"] == "noted"


# ---------------------------------------------------------------------------
# _first_tool_tag_pos
# ---------------------------------------------------------------------------


def test_first_tool_tag_pos_returns_minus_one_when_no_tags():
    assert _first_tool_tag_pos("hello world", ["screen", "remember"]) == -1


def test_first_tool_tag_pos_finds_earliest():
    buf = "text<remember>note</remember><screen><svg/></screen>"
    pos = _first_tool_tag_pos(buf, ["screen", "remember"])
    assert pos == buf.index("<remember>")


def test_first_tool_tag_pos_respects_start():
    buf = "<screen>svg</screen>"
    assert _first_tool_tag_pos(buf, ["screen"], start=5) == -1


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.anthropic.Anthropic")
def test_send_message_returns_reply(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text="Hello, I'm Sudo!")]
    )

    history = []
    text, calls = send_message(mock_client, history, "Hello")

    assert text == "Hello, I'm Sudo!"
    assert calls == {}


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

    messages_sent = mock_client.messages.create.call_args.kwargs["messages"]
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

    assert mock_client.messages.create.call_args.kwargs["system"] == SYSTEM_PROMPT


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
def test_send_message_strips_tool_tags_from_history(mock_anthropic):
    """Tool tag content is not stored in history — only the text reply."""
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
def test_send_message_returns_screen_call_when_present(mock_anthropic):
    svg = "<svg><rect width='10' height='10'/></svg>"
    raw = f"<screen>{svg}</screen>\nRed screen."
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text=raw)])

    history = []
    text, calls = send_message(mock_client, history, "Hi")

    assert text == "Red screen."
    assert calls["screen"] == svg


# ---------------------------------------------------------------------------
# _dispatch_tool_calls
# ---------------------------------------------------------------------------


def test_dispatch_tool_calls_runs_inline_handler():
    called_with = []
    tools = {
        "remember": MagicMock(
            main_thread=False, handler=lambda c: called_with.append(c)
        )
    }
    _dispatch_tool_calls({"remember": "a note"}, queue.Queue(), tools)
    assert called_with == ["a note"]


def test_dispatch_tool_calls_queues_main_thread_handler():
    q = queue.Queue()
    tool = MagicMock(main_thread=True)
    tools = {"screen": tool}
    _dispatch_tool_calls({"screen": "<svg/>"}, q, tools)
    assert not q.empty()
    queued_tool, content = q.get_nowait()
    assert queued_tool is tool
    assert content == "<svg/>"


def test_dispatch_tool_calls_skips_none_content():
    called = []
    tools = {
        "remember": MagicMock(main_thread=False, handler=lambda c: called.append(c))
    }
    _dispatch_tool_calls({"remember": None}, queue.Queue(), tools)
    assert called == []


# ---------------------------------------------------------------------------
# _make_tools / _handle_remember
# ---------------------------------------------------------------------------


def test_handle_remember_calls_append_note():
    mock_client = MagicMock()
    renderer = MagicMock()
    screen_state = ScreenState()

    with patch("chat.append_note") as mock_append:
        tools = _make_tools(renderer, screen_state, mock_client)
        tools["remember"].handler("An interesting observation.")

    mock_append.assert_called_once_with(mock_client, "An interesting observation.")


# ---------------------------------------------------------------------------
# _expression_loop
# ---------------------------------------------------------------------------


class _Stop(BaseException):
    pass


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_queues_screen_when_returned(mock_sleep):
    svg = "<svg><rect width='10' height='10'/></svg>"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(text=f"<screen>{svg}</screen>")]
    )
    action_queue = queue.Queue()
    screen_state = ScreenState()
    tools = _make_tools(MagicMock(), screen_state, mock_client)

    with pytest.raises(_Stop):
        _expression_loop(mock_client, action_queue, tools, "system", [], screen_state)

    assert not action_queue.empty()
    _, content = action_queue.get_nowait()
    assert content == svg


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_skips_queue_when_no_tool_calls(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
    action_queue = queue.Queue()
    screen_state = ScreenState()
    tools = _make_tools(MagicMock(), screen_state, mock_client)

    with pytest.raises(_Stop):
        _expression_loop(mock_client, action_queue, tools, "system", [], screen_state)

    assert action_queue.empty()


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_includes_history_snapshot(mock_sleep):
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
    history = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hey"},
    ]
    screen_state = ScreenState()
    tools = _make_tools(MagicMock(), screen_state, mock_client)

    with pytest.raises(_Stop):
        _expression_loop(
            mock_client, queue.Queue(), tools, "system", history, screen_state
        )

    messages_sent = mock_client.messages.create.call_args.kwargs["messages"]
    assert messages_sent[0] == {"role": "user", "content": "hi"}


@patch("chat.time.sleep", side_effect=[None, _Stop()])
def test_expression_loop_includes_screen_in_system_prompt(mock_sleep):
    svg = "<svg><rect/></svg>"
    mock_client = MagicMock()
    mock_client.messages.create.return_value = MagicMock(content=[MagicMock(text="")])
    screen_state = ScreenState(svg=svg)
    tools = _make_tools(MagicMock(), screen_state, mock_client)

    with pytest.raises(_Stop):
        _expression_loop(mock_client, queue.Queue(), tools, "base", [], screen_state)

    system_sent = mock_client.messages.create.call_args.kwargs["system"]
    assert svg in system_sent


# ---------------------------------------------------------------------------
# ScreenState / _system_with_screen
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# run_chat integration
# ---------------------------------------------------------------------------


@patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
@patch("chat.save_history")
@patch("chat.load_summaries", return_value=[])
@patch("chat.load_notes", return_value=None)
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
    _mock_load_notes,
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


def test_save_to_gallery_writes_svg(tmp_path):
    svg = "<svg><rect/></svg>"
    with patch("chat.GALLERY_DIR", str(tmp_path / "gallery")):
        _save_to_gallery(svg)
    files = list((tmp_path / "gallery").rglob("*.svg"))
    assert len(files) == 1
    assert files[0].read_text() == svg


def test_save_to_gallery_organizes_by_date(tmp_path):
    svg = "<svg/>"
    with patch("chat.GALLERY_DIR", str(tmp_path / "gallery")):
        _save_to_gallery(svg)
    date_dirs = list((tmp_path / "gallery").iterdir())
    assert len(date_dirs) == 1
    # directory name matches YYYY-MM-DD
    assert len(date_dirs[0].name) == 10
    assert date_dirs[0].name[4] == "-"


def test_save_to_gallery_not_called_when_disabled(tmp_path):
    svg = "<svg/>"
    with patch("chat.GALLERY_ENABLED", False):
        with patch("chat.GALLERY_DIR", str(tmp_path / "gallery")):
            from chat import _render_and_save

            mock_renderer = MagicMock()
            _render_and_save(mock_renderer, svg, ScreenState())
    assert not (tmp_path / "gallery").exists()


def test_save_to_gallery_called_when_enabled(tmp_path):
    svg = "<svg/>"
    with patch("chat.GALLERY_ENABLED", True):
        with patch("chat.GALLERY_DIR", str(tmp_path / "gallery")):
            from chat import _render_and_save

            mock_renderer = MagicMock()
            _render_and_save(mock_renderer, svg, ScreenState())
    assert len(list((tmp_path / "gallery").rglob("*.svg"))) == 1
