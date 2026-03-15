from unittest.mock import MagicMock, patch

from screen import ScreenRenderer


@patch("screen._CAIROSVG_AVAILABLE", True)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_init_opens_display_immediately(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()

    mock_pygame.init.assert_called_once()
    mock_pygame.display.set_mode.assert_called_once()
    renderer.stop()


@patch("screen._CAIROSVG_AVAILABLE", True)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.cairosvg", create=True)
@patch("screen.pygame")
def test_render_converts_svg_and_blits(mock_pygame, mock_cairosvg):
    mock_pygame.display.set_mode.return_value = MagicMock()
    mock_cairosvg.svg2png.return_value = b"fake png"
    renderer = ScreenRenderer()

    renderer.render("<svg></svg>")

    mock_cairosvg.svg2png.assert_called_once()
    mock_pygame.image.load.assert_called_once()
    renderer._surface.blit.assert_called_once()
    renderer.stop()


@patch("screen._CAIROSVG_AVAILABLE", True)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.cairosvg", create=True)
@patch("screen.pygame")
def test_render_does_not_reinitialize_on_subsequent_calls(mock_pygame, mock_cairosvg):
    mock_pygame.display.set_mode.return_value = MagicMock()
    mock_cairosvg.svg2png.return_value = b"fake png"
    renderer = ScreenRenderer()

    renderer.render("<svg></svg>")
    renderer.render("<svg></svg>")

    mock_pygame.init.assert_called_once()
    renderer.stop()


@patch("screen._CAIROSVG_AVAILABLE", True)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_skips_when_display_unavailable(mock_pygame):
    mock_pygame.error = Exception
    mock_pygame.display.set_mode.side_effect = Exception("No display")
    renderer = ScreenRenderer()

    renderer.render("<svg></svg>")  # should not raise

    assert renderer._surface is None


@patch("screen._PYGAME_AVAILABLE", False)
def test_render_skips_when_pygame_not_installed():
    renderer = ScreenRenderer()

    renderer.render("<svg></svg>")  # should not raise

    assert renderer._surface is None


@patch("screen._CAIROSVG_AVAILABLE", False)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_skips_when_cairosvg_not_installed(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()

    renderer.render("<svg></svg>")  # should not raise

    renderer._surface.blit.assert_not_called()
    renderer.stop()


@patch("screen._CAIROSVG_AVAILABLE", True)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_stop_calls_pygame_quit(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()

    renderer.stop()

    mock_pygame.quit.assert_called_once()
    assert renderer._surface is None


@patch("screen._CAIROSVG_AVAILABLE", True)
@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.cairosvg", create=True)
@patch("screen.pygame")
def test_save_writes_png(mock_pygame, mock_cairosvg, tmp_path):
    mock_pygame.display.set_mode.return_value = MagicMock()
    mock_cairosvg.svg2png.return_value = b"fake png"
    renderer = ScreenRenderer()
    renderer.render("<svg></svg>")

    renderer.save(str(tmp_path / "screen.png"))

    mock_pygame.image.save.assert_called_once()
    renderer.stop()


@patch("screen._PYGAME_AVAILABLE", False)
def test_save_is_noop_when_not_initialized():
    renderer = ScreenRenderer()

    renderer.save("/tmp/screen.png")  # should not raise


@patch("screen._PYGAME_AVAILABLE", False)
def test_stop_is_noop_when_not_initialized():
    renderer = ScreenRenderer()

    renderer.stop()  # should not raise
