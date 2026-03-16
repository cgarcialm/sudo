import io
import pathlib
import sys

try:
    import cairosvg

    _CAIROSVG_AVAILABLE = True
except (ImportError, OSError):
    _CAIROSVG_AVAILABLE = False

try:
    import pygame

    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

from config import SCREEN_FULLSCREEN as _SCREEN_FULLSCREEN
from config import SCREEN_SIZE as _SCREEN_SIZE


class ScreenRenderer:
    """Renders SVG content in a pygame window.

    Initializes the display immediately on construction.
    Silently skips rendering if pygame or cairosvg is unavailable.
    Call tick() from the main thread regularly to keep the window responsive.
    """

    def __init__(self):
        self._surface = None
        self._init_display()

    def _init_display(self):
        if not _PYGAME_AVAILABLE:
            return
        try:
            pygame.init()
            if _SCREEN_FULLSCREEN:
                size, flags = (0, 0), pygame.FULLSCREEN
            else:
                size, flags = (_SCREEN_SIZE, _SCREEN_SIZE), 0
            self._surface = pygame.display.set_mode(size, flags)
            pygame.display.set_caption("Sudo")
            self._surface.fill((0, 0, 0))
            pygame.display.flip()
        except pygame.error:
            pygame.quit()
            self._surface = None

    def tick(self):
        """Pump pygame events. Must be called from the main thread."""
        if self._surface is not None:
            pygame.event.pump()

    def render(self, svg_string):
        """Render an SVG string to the screen. No-op if display or cairosvg missing."""
        if self._surface is None or not _CAIROSVG_AVAILABLE:
            return
        try:
            w, h = self._surface.get_size()
            png_bytes = cairosvg.svg2png(
                bytestring=svg_string.encode(),
                output_width=w,
                output_height=h,
            )
            img = pygame.transform.scale(
                pygame.image.load(io.BytesIO(png_bytes)), (w, h)
            )
            self._surface.blit(img, (0, 0))
            pygame.display.flip()
        except Exception as e:
            print(f"[screen] render failed: {e}", file=sys.stderr)

    def save(self, path):
        """Save the current screen as a PNG. No-op if display is unavailable."""
        if self._surface is None:
            return
        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self._surface, path)

    def stop(self):
        """Shut down pygame if it was initialized."""
        if self._surface is not None:
            pygame.quit()
            self._surface = None
