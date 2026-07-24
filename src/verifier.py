"""Rule-based verification of a proposed operation.

The workshop is explicit (68:03): "the best form of verification is rule-based."
Not an LLM judging its own work — deterministic rules that either hold or don't.
A rejection returns text, because that text is fed straight back to the agent
as the context for its next attempt.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Set

from .operations import AddColumn, DeleteRows, Operation, ReadColumn, SetCell
from .table import Table

ROW_CAP = 100  # a task-defined guardrail: refuse edits to oversized tables


@dataclass
class Verdict:
    ok: bool
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


def verify(op: Operation, table: Table, columns_read: Set[str]) -> Verdict:
    """Return ok, or a reason the operation must not be applied."""
    if isinstance(op, ReadColumn):
        if op.column not in table.columns:
            return Verdict(False, f"cannot read {op.column!r}; columns are {table.columns}")
        return Verdict(True)

    # any mutation on an oversized table is refused outright
    if len(table.rows) > ROW_CAP:
        return Verdict(False, f"table has {len(table.rows)} rows, over the {ROW_CAP} cap; refuse to edit")

    if isinstance(op, SetCell):
        if op.column not in table.columns:
            return Verdict(False, f"column {op.column!r} does not exist; columns are {table.columns}")
        if op.column not in columns_read:
            return Verdict(False, f"write to {op.column!r} before reading it (read-before-write)")
        if not (0 <= op.row < len(table.rows)):
            return Verdict(False, f"row {op.row} out of range 0..{len(table.rows) - 1}")
        if op.value.strip() == "":
            return Verdict(False, "refusing to write an empty/null value")
        return Verdict(True)

    if isinstance(op, AddColumn):
        if op.column in table.columns:
            return Verdict(False, f"column {op.column!r} already exists")
        if not op.column.strip():
            return Verdict(False, "column name is empty")
        return Verdict(True)

    if isinstance(op, DeleteRows):
        if op.where_column not in table.columns:
            return Verdict(False, f"column {op.where_column!r} does not exist; columns are {table.columns}")
        return Verdict(True)  # allowed — but destructive, so the loop checkpoints first

    return Verdict(False, f"unknown operation {type(op).__name__}")
