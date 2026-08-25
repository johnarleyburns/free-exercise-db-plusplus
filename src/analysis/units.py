"""Explicit, conservative quantity conversions for derived analysis."""
from __future__ import annotations

from typing import Any


class UnitError(ValueError):
    """Raised when a quantity cannot be safely normalized."""


_CONVERSIONS: dict[tuple[str, str], float] = {
    ("kg", "kg"): 1.0, ("g", "kg"): 0.001, ("lb", "kg"): 0.45359237,
    ("m", "m"): 1.0, ("cm", "m"): 0.01, ("km", "m"): 1000.0,
    ("s", "s"): 1.0, ("min", "s"): 60.0, ("h", "s"): 3600.0,
}


def normalize_quantity(quantity: dict[str, Any], target_unit: str) -> float:
    """Convert a known quantity to a compatible target unit."""
    if not isinstance(quantity, dict) or not {"value", "unit"} <= quantity.keys():
        raise UnitError("quantity must contain value and unit")
    source = str(quantity["unit"]).strip().lower()
    target = target_unit.strip().lower()
    try:
        factor = _CONVERSIONS[(source, target)]
    except KeyError as exc:
        raise UnitError(f"incompatible or unknown units: {source!r} -> {target!r}") from exc
    return float(quantity["value"]) * factor


def compatible_unit(unit: str, target_unit: str) -> bool:
    return (unit.strip().lower(), target_unit.strip().lower()) in _CONVERSIONS


__all__ = ["UnitError", "compatible_unit", "normalize_quantity"]
