"""System tray integration."""

from __future__ import annotations

from pathlib import Path
import threading
from typing import Callable

from PIL import Image, ImageDraw
import pystray

from . import APP_NAME


class TrayIcon:
    """pystray wrapper for the app tray icon and menu."""

    def __init__(
        self,
        project_root: Path,
        on_settings: Callable[[], None],
        on_exit: Callable[[], None],
        on_uninstall: Callable[[], None],
    ) -> None:
        self.project_root = project_root
        self.on_settings = on_settings
        self.on_exit = on_exit
        self.on_uninstall = on_uninstall
        self.icon: pystray.Icon | None = None
        self.thread: threading.Thread | None = None

    def start(self) -> None:
        """Start the tray icon in a Windows-safe background thread."""

        menu = pystray.Menu(
            pystray.MenuItem("Settings", self._handle_settings),
            pystray.MenuItem("Uninstall", self._handle_uninstall),
            pystray.MenuItem("Exit", self._handle_exit),
        )
        self.icon = pystray.Icon(
            "phrase-auto-correct",
            icon=self._load_icon(),
            title=APP_NAME,
            menu=menu,
        )
        self.thread = threading.Thread(
            target=self.icon.run,
            name="PhraseTrayIcon",
            daemon=True,
        )
        self.thread.start()

    def stop(self) -> None:
        """Stop the tray icon."""

        if self.icon:
            self.icon.stop()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=2)

    def _handle_settings(self, _icon: pystray.Icon, _item: object) -> None:
        self.on_settings()

    def _handle_exit(self, _icon: pystray.Icon, _item: object) -> None:
        self.on_exit()

    def _handle_uninstall(self, _icon: pystray.Icon, _item: object) -> None:
        self.on_uninstall()

    def _load_icon(self) -> Image.Image:
        icon_path = self.project_root / "icon.jpg"
        if icon_path.exists():
            with Image.open(icon_path) as image:
                return self._fit_icon(image)
        return self._fallback_icon()

    @staticmethod
    def _fit_icon(image: Image.Image) -> Image.Image:
        source = image.convert("RGBA")
        source.thumbnail((64, 64))
        canvas = Image.new("RGBA", (64, 64), (255, 255, 255, 0))
        x = (64 - source.width) // 2
        y = (64 - source.height) // 2
        canvas.alpha_composite(source, (x, y))
        return canvas

    @staticmethod
    def _fallback_icon() -> Image.Image:
        image = Image.new("RGBA", (64, 64), "#2563eb")
        draw = ImageDraw.Draw(image)
        draw.rectangle((14, 16, 50, 24), fill="white")
        draw.rectangle((14, 30, 44, 38), fill="white")
        draw.rectangle((14, 44, 36, 52), fill="white")
        return image
