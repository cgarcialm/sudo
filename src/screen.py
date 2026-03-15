import io
import pathlib
import threading
import time

try:
    import cairosvg

    _CAIROSVG_AVAILABLE = True
except ImportError:
    _CAIROSVG_AVAILABLE = False

try:
    import pygame

    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

from config import SCREEN_SIZE as _SCREEN_SIZE


class ScreenRenderer:
    """Renders SVG content in a pygame window.

    Initializes the display immediately on construction.
    Silently skips rendering if pygame or cairosvg is unavailable.
    Keeps the window alive with a background event-pump thread.
    """

    def __init__(self):
        self._surface = None
        self._stop_event = threading.Event()
        self._init_display()

    def _init_display(self):
        if not _PYGAME_AVAILABLE:
            return
        try:
            pygame.init()
            self._surface = pygame.display.set_mode((_SCREEN_SIZE, _SCREEN_SIZE))
            pygame.display.set_caption("Sudo")
            self._surface.fill((0, 0, 0))
            pygame.display.flip()
            self._start_event_pump()
        except pygame.error:
            pygame.quit()
            self._surface = None

    def _start_event_pump(self):
        def pump():
            while not self._stop_event.is_set():
                pygame.event.pump()
                time.sleep(0.1)

        threading.Thread(target=pump, daemon=True).start()

    def render(self, svg_string):
        """Render an SVG string to the screen. No-op if display or cairosvg missing."""
        if self._surface is None or not _CAIROSVG_AVAILABLE:
            return
        try:
            png_bytes = cairosvg.svg2png(
                bytestring=svg_string.encode(),
                output_width=_SCREEN_SIZE,
                output_height=_SCREEN_SIZE,
            )
            img = pygame.image.load(io.BytesIO(png_bytes))
            self._surface.blit(img, (0, 0))
            pygame.display.flip()
        except Exception:
            pass

    def save(self, path):
        """Save the current screen as a PNG. No-op if display is unavailable."""
        if self._surface is None:
            return
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self._surface, path)

    def stop(self):
        """Shut down pygame if it was initialized."""
        self._stop_event.set()
        if self._surface is not None:
            pygame.quit()
            self._surface = None
