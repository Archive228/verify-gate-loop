"""A tiny in-memory table with checkpoint/rollback.

State is reversible on purpose. The workshop's point (70:00): code edits are
reversible (git), but real-world actions often aren't, so a long-running agent
needs an explicit checkpoint it can roll back to when a step goes wrong.
"""
from __future__ import annotations

import copy
import csv
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Table:
    columns: list[str]
    rows: list[dict[str, str]]
    _checkpoints: list[tuple[list[str], list[dict[str, str]]]] = field(default_factory=list)

    @classmethod
    def from_csv(cls, path: str | Path) -> "Table":
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            rows = [dict(r) for r in reader]
            columns = list(reader.fieldnames or [])
        return cls(columns=columns, rows=rows)

    def checkpoint(self) -> int:
        """Snapshot current state. Returns the checkpoint index."""
        self._checkpoints.append((list(self.columns), copy.deepcopy(self.rows)))
        return len(self._checkpoints) - 1

    def rollback(self) -> None:
        """Restore the most recent checkpoint."""
        if not self._checkpoints:
            raise RuntimeError("nothing to roll back to")
        self.columns, self.rows = self._checkpoints.pop()

    def snapshot(self) -> str:
        head = ",".join(self.columns)
        body = "\n".join(",".join(r.get(c, "") for c in self.columns) for r in self.rows)
        return f"{head}\n{body}" if body else head
