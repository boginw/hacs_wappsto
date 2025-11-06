"""Represents a Wappsto device."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WappstoValue:
    """Represents a Wappsto value."""

    wappsto_id: str
    name: str
    type: str
    permission: str
    data: str | None = None
    unit: str | None = None
    state_read: str | None = None
    state_write: str | None = None


@dataclass
class WappstoDevice:
    """Represents a Wappsto device."""

    wappsto_id: str
    name: str
    values: dict[str, WappstoValue]

    def get_value(self, value_id: str) -> WappstoValue | None:
        """Return the value with the given ID."""
        return self.values.get(value_id)
