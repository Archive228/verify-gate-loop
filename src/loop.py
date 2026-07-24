"""The loop: gather -> act -> verify. Nothing is applied until verify passes.

Straight from the workshop (22:20): "here is the three parts to an agent loop.
So, first, it's gather context. Second is taking action, and the third is
verifying the work." Here gather is an explicit ReadColumn op, act is a mutation,
and every op — gather included — passes through the same verify gate
(82:10: put verification "in as many places as you can").
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set

from .operations import DeleteRows, Operation, ReadColumn
from .table import Table
from .verifier import verify


@dataclass
class Step:
    n: int
    op_repr: str
    accepted: bool
    note: str


@dataclass
class RunLog:
    steps: List[Step] = field(default_factory=list)

    @property
    def accepted(self) -> int:
        return sum(s.accepted for s in self.steps)

    @property
    def rejected(self) -> int:
        return sum(not s.accepted for s in self.steps)

    @property
    def reject_reasons(self) -> List[str]:
        return [s.note for s in self.steps if not s.accepted]


# An agent proposes the next op given the columns it has read and the last rejection.
Agent = Callable[[List[str], Optional[str]], Optional[Operation]]


def run_loop(
    table: Table,
    agent: Agent,
    max_steps: int = 16,
    on_event: Optional[Callable[[str], None]] = None,
) -> RunLog:
    emit = on_event or (lambda _m: None)
    log = RunLog()
    columns_read: Set[str] = set()
    last_reason: Optional[str] = None
    n = 0

    while n < max_steps:
        # 1. GATHER: the agent decides its next op (which may itself be a read)
        op = agent(list(table.columns), last_reason)
        if op is None:
            emit("agent: done")
            break
        n += 1

        # 2. ACT is only *proposed* here; nothing mutates yet.
        # 3. VERIFY: the gate. A rejection never touches the table.
        verdict = verify(op, table, columns_read)
        if not verdict:
            last_reason = verdict.reason
            log.steps.append(Step(n, repr(op), False, verdict.reason))
            emit(f"step {n}: REJECT {repr(op)}\n         -> {verdict.reason}")
            continue

        # destructive ops are reversible only because we checkpoint first (70:00)
        if isinstance(op, DeleteRows):
            table.checkpoint()
            emit(f"step {n}: checkpoint (destructive op ahead, rollback available)")

        _apply(op, table, columns_read)
        last_reason = None
        kind = "READ  " if isinstance(op, ReadColumn) else "APPLY "
        log.steps.append(Step(n, repr(op), True, "applied"))
        emit(f"step {n}: {kind} {repr(op)}")

    return log


def _apply(op: Operation, table: Table, columns_read: Set[str]) -> None:
    from .operations import AddColumn, DeleteRows, ReadColumn, SetCell

    if isinstance(op, ReadColumn):
        columns_read.add(op.column)
    elif isinstance(op, SetCell):
        table.rows[op.row][op.column] = op.value
    elif isinstance(op, AddColumn):
        table.columns.append(op.column)
        for row in table.rows:
            row[op.column] = op.default
    elif isinstance(op, DeleteRows):
        table.rows = [r for r in table.rows if r.get(op.where_column) != op.equals]
