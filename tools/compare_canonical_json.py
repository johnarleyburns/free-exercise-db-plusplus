#!/usr/bin/env python3
"""Compare two canonical fixture JSON documents.

Only JSON object member order and numeric representation are insignificant.
Arrays, null/missing fields, and every semantic value remain significant.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any


def _number_equal(left: Any, right: Any) -> bool:
    return (isinstance(left, (int, float)) and not isinstance(left, bool)
            and isinstance(right, (int, float)) and not isinstance(right, bool)
            and left == right and not (isinstance(left, float) and math.isnan(left))
            and not (isinstance(right, float) and math.isnan(right)))


def _difference(left: Any, right: Any, path: str = "$") -> str | None:
    if _number_equal(left, right):
        return None
    if type(left) is not type(right):
        return f"{path}: type/value differs ({type(left).__name__} != {type(right).__name__})"
    if isinstance(left, dict):
        left_keys, right_keys = set(left), set(right)
        missing = sorted(left_keys - right_keys)
        extra = sorted(right_keys - left_keys)
        if missing or extra:
            return f"{path}: keys differ (missing={missing}, extra={extra})"
        for key in sorted(left_keys):
            difference = _difference(left[key], right[key], f"{path}.{key}")
            if difference:
                return difference
        return None
    if isinstance(left, list):
        if len(left) != len(right):
            return f"{path}: array length differs ({len(left)} != {len(right)})"
        for index, (left_value, right_value) in enumerate(zip(left, right)):
            difference = _difference(left_value, right_value, f"{path}[{index}]")
            if difference:
                return difference
        return None
    if left != right:
        return f"{path}: values differ ({left!r} != {right!r})"
    return None


def compare(left: Any, right: Any) -> str | None:
    """Return the first semantic difference, or ``None`` when equal."""
    return _difference(left, right)


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(f"usage: {argv[0]} EXPECTED ACTUAL", file=sys.stderr)
        return 2
    expected = json.loads(Path(argv[1]).read_text())
    actual = json.loads(Path(argv[2]).read_text())
    difference = compare(expected, actual)
    if difference:
        print(difference, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
