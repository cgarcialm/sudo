try:
    import pygame

    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False

GRID_SIZE = 16
PIXEL_SIZE = 20


class ScreenRenderer:
    """Renders a 16x16 hex-color grid in a pygame window.

    Silently skips rendering if pygame is unavailable or no display is present.
    """

    def __init__(self, pixel_size=PIXEL_SIZE):
        self.pixel_size = pixel_size
        self._surface = None
        self._init_tried = False

    def _init_display(self):
        self._init_tried = True
        if not _PYGAME_AVAILABLE:
            return
        try:
            pygame.init()
            size = self.pixel_size * GRID_SIZE
            self._surface = pygame.display.set_mode((size, size))
            pygame.display.set_caption("Sudo")
        except pygame.error:
            pygame.quit()
            self._surface = None

    def render(self, grid):
        """Draw the 16x16 grid. No-op if display is unavailable."""
        if not self._init_tried:
            self._init_display()
        if self._surface is None:
            return
        for row_idx, row in enumerate(grid):
            for col_idx, hex_color in enumerate(row):
                color = pygame.Color(hex_color)
                pygame.draw.rect(
                    self._surface,
                    color,
                    (
                        col_idx * self.pixel_size,
                        row_idx * self.pixel_size,
                        self.pixel_size,
                        self.pixel_size,
                    ),
                )
        pygame.display.flip()
        pygame.event.pump()

    def save(self, path):
        """Save the current grid as a PNG. No-op if display is unavailable."""
        if self._surface is None:
            return
        import pathlib

        pathlib.Path(path).parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(self._surface, path)

    def stop(self):
        """Shut down pygame if it was initialized."""
        if self._surface is not None:
            pygame.quit()
            self._surface = None
