"""Platform-independent translation of MainActivity's comparison and scan state."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, Set, Tuple


class ScanState(Enum):
    WAITING_BARCODE1 = auto()
    WAITING_BARCODE2 = auto()
    SHOWING_RESULT = auto()


def matches_with_one_extra_zero(shorter: str, longer: str) -> bool:
    return len(longer) == len(shorter) + 1 and any(
        char == "0" and longer[:i] + longer[i + 1:] == shorter
        for i, char in enumerate(longer)
    )


def barcodes_match(a: str, b: str, tolerance_contains: bool = True,
                   tolerance_extra_zero: bool = True) -> bool:
    if a == b:
        return True
    if tolerance_contains and (a in b or b in a):
        return True
    return tolerance_extra_zero and (
        matches_with_one_extra_zero(a, b) or matches_with_one_extra_zero(b, a)
    )


def differing_indices(a: str, b: str) -> Tuple[Set[int], Set[int]]:
    """Use the original LCS algorithm, including its deletion-first tie breaking."""
    n, m = len(a), len(b)
    lcs = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n - 1, -1, -1):
        for j in range(m - 1, -1, -1):
            lcs[i][j] = (lcs[i + 1][j + 1] + 1 if a[i] == b[j]
                         else max(lcs[i + 1][j], lcs[i][j + 1]))
    da, db = set(), set()
    i = j = 0
    while i < n and j < m:
        if a[i] == b[j]:
            i += 1
            j += 1
        elif lcs[i + 1][j] >= lcs[i][j + 1]:
            da.add(i)
            i += 1
        else:
            db.add(j)
            j += 1
    da.update(range(i, n))
    db.update(range(j, m))
    return da, db


def highlight_ranges(code: str, indices: Set[int]):
    """Contiguous, exclusive-end ranges in Android's UTF-16 coordinates."""
    offsets = [0]
    for char in code:
        offsets.append(offsets[-1] + len(char.encode("utf-16-le")) // 2)
    start = 0
    while start < len(code):
        if start not in indices:
            start += 1
            continue
        end = start + 1
        while end < len(code) and end in indices:
            end += 1
        yield offsets[start], offsets[end]
        start = end


def normalize_scan(raw: str) -> str:
    """TextWatcher fallback: take text before the first CR or LF, then trim."""
    end = next((i for i, char in enumerate(raw) if char in "\r\n"), len(raw))
    return raw[:end].strip()


@dataclass(frozen=True)
class ScanResult:
    first: str
    second: str
    match: bool


class ScanSession:
    def __init__(self):
        self.reset()

    def reset(self):
        self.state = ScanState.WAITING_BARCODE1
        self.barcode1: Optional[str] = None
        self.result: Optional[ScanResult] = None

    def consume(self, raw: str, settings) -> Optional[ScanResult]:
        code = normalize_scan(raw)
        if not code or self.state is ScanState.SHOWING_RESULT:
            return None
        if self.state is ScanState.WAITING_BARCODE1:
            self.barcode1 = code
            self.state = ScanState.WAITING_BARCODE2
            return None
        self.result = ScanResult(self.barcode1 or "", code, barcodes_match(
            self.barcode1 or "", code, settings.tolerance_contains,
            settings.tolerance_extra_zero,
        ))
        self.state = ScanState.SHOWING_RESULT
        return self.result
