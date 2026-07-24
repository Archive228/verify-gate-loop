"""The actions an agent may propose. Each is data, not a method call — so the
verifier gets to inspect and reject it BEFORE it ever touches the table.

ReadColumn is the "gather" step made explicit: the agent must read a column
before it is allowed to write it. That is why read-before-write can actually be
enforced here (68:22) instead of being a rule that never fires.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Union


@dataclass(frozen=True)
class ReadColumn:
    """Gather. Non-mutating; marks the column as read."""
    column: str


@dataclass(frozen=True)
class SetCell:
    row: int
    column: str
    value: str


@dataclass(frozen=True)
class AddColumn:
    column: str
    default: str = ""


@dataclass(frozen=True)
class DeleteRows:
    """Destructive. This is the one that needs a checkpoint before it runs."""
    where_column: str
    equals: str


Operation = Union[ReadColumn, SetCell, AddColumn, DeleteRows]
