from __future__ import annotations

from pathlib import Path


class KillSwitch:
    def __init__(self, path: str | Path = ".kill_switch") -> None:
        self.path = Path(path)

    def active(self) -> bool:
        return self.path.exists()

    def activate(self) -> None:
        self.path.write_text("active
")

    def deactivate(self) -> None:
        if self.path.exists():
            self.path.unlink()
