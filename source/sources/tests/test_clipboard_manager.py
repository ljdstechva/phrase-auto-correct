from __future__ import annotations

from pathlib import Path
import sys
import tkinter as tk
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.clipboard_manager import ClipboardManager


class ClipboardManagerTests(unittest.TestCase):
    def test_text_set_read_and_restore(self) -> None:
        root = tk.Tk()
        root.withdraw()
        manager = ClipboardManager(int(root.winfo_id()))
        snapshot = manager.snapshot()
        try:
            manager.set_text("Phrase Auto-correct clipboard test")
            self.assertEqual(
                manager.get_text(),
                "Phrase Auto-correct clipboard test",
            )
        finally:
            manager.restore(snapshot)
            root.destroy()


if __name__ == "__main__":
    unittest.main()
