from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple

@dataclass(frozen=True)
class LineCol:
    line: int
    col: int

class LineMap:
    def __init__(self, src: str):
        self.src = src
        self.line_starts: List[int] = [0]
        for i, ch in enumerate(src):
            if ch == "\n":
                self.line_starts.append(i + 1)

    def pos_to_linecol(self, pos: int) -> LineCol:
        lo, hi = 0, len(self.line_starts) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if self.line_starts[mid] <= pos:
                lo = mid + 1
            else:
                hi = mid - 1
        idx = max(0, lo - 1)
        start = self.line_starts[idx]
        return LineCol(line=idx + 1, col=pos - start + 1)

    def span_to_linecols(self, start: int, end: int) -> Tuple[LineCol, LineCol]:
        return self.pos_to_linecol(start), self.pos_to_linecol(max(start, end-1))
