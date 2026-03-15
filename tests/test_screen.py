from unittest.mock import MagicMock, patch

from screen import GRID_SIZE, PIXEL_SIZE, ScreenRenderer


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_initializes_display_on_first_call(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()
    grid = [["#000000"] * GRID_SIZE for _ in range(GRID_SIZE)]

    renderer.render(grid)

    mock_pygame.init.assert_called_once()
    mock_pygame.display.set_mode.assert_called_once_with(
        (PIXEL_SIZE * GRID_SIZE, PIXEL_SIZE * GRID_SIZE)
    )


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_draws_all_pixels(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()
    grid = [["#ff0000"] * GRID_SIZE for _ in range(GRID_SIZE)]

    renderer.render(grid)

    assert mock_pygame.draw.rect.call_count == GRID_SIZE * GRID_SIZE


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_does_not_reinitialize_on_subsequent_calls(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()
    grid = [["#000000"] * GRID_SIZE for _ in range(GRID_SIZE)]

    renderer.render(grid)
    renderer.render(grid)

    mock_pygame.init.assert_called_once()


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_skips_when_display_unavailable(mock_pygame):
    # make pygame.error a real exception so the except clause in screen.py works
    mock_pygame.error = Exception
    mock_pygame.display.set_mode.side_effect = Exception("No display")
    renderer = ScreenRenderer()
    grid = [["#000000"] * GRID_SIZE for _ in range(GRID_SIZE)]

    renderer.render(grid)  # should not raise

    mock_pygame.draw.rect.assert_not_called()


@patch("screen._PYGAME_AVAILABLE", False)
def test_render_skips_when_pygame_not_installed():
    renderer = ScreenRenderer()
    grid = [["#000000"] * GRID_SIZE for _ in range(GRID_SIZE)]

    renderer.render(grid)  # should not raise

    assert renderer._surface is None


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_stop_calls_pygame_quit(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer()
    grid = [["#000000"] * GRID_SIZE for _ in range(GRID_SIZE)]
    renderer.render(grid)

    renderer.stop()

    mock_pygame.quit.assert_called_once()
    assert renderer._surface is None


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_stop_is_noop_when_not_initialized(mock_pygame):
    renderer = ScreenRenderer()

    renderer.stop()  # never rendered, should not raise

    mock_pygame.quit.assert_not_called()


@patch("screen._PYGAME_AVAILABLE", True)
@patch("screen.pygame")
def test_render_uses_custom_pixel_size(mock_pygame):
    mock_pygame.display.set_mode.return_value = MagicMock()
    renderer = ScreenRenderer(pixel_size=10)
    grid = [["#000000"] * GRID_SIZE for _ in range(GRID_SIZE)]

    renderer.render(grid)

    mock_pygame.display.set_mode.assert_called_once_with(
        (10 * GRID_SIZE, 10 * GRID_SIZE)
    )
