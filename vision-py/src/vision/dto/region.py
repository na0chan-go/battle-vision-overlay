from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Region:
    name: str
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height
