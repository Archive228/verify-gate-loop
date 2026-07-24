"""Runnable demo. `./run.sh` lands here."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.loop import run_loop              # noqa: E402
from src.scripted_agent import ScriptedAgent  # noqa: E402
from src.table import Table                # noqa: E402

BAR = "─" * 66


def main() -> int:
    data = Path(__file__).resolve().parent.parent / "data" / "sales.csv"
    table = Table.from_csv(data)

    print(BAR)
    print("verify-gate-loop  —  gather -> act -> VERIFY (rule-based gate)")
    print(f"table: {data.name}  columns={table.columns}  rows={len(table.rows)}")
    print(BAR)

    rows_before = len(table.rows)
    log = run_loop(table, ScriptedAgent(), on_event=print)

    print(BAR)
    print(f"applied {log.accepted}, rejected {log.rejected}")
    print("gate blocked:")
    for r in log.reject_reasons:
        print(f"  - {r}")
    print()
    print("table after the loop:")
    print(_indent(table.snapshot()))

    # 70:00 — destructive edits are reversible only because we checkpointed.
    print()
    print("rollback demo: the EU delete was checkpointed, so we can undo it")
    rows_after_delete = len(table.rows)
    table.rollback()
    print(f"  rows: {rows_before} -> {rows_after_delete} (after delete) -> {len(table.rows)} (after rollback)")
    print(BAR)

    # honest success criteria: every rule fired, and rollback restored state
    reasons = " ".join(log.reject_reasons)
    ok = (
        log.rejected == 3
        and "does not exist" in reasons
        and "read-before-write" in reasons
        and "empty/null" in reasons
        and len(table.rows) == rows_before
    )
    print("OK" if ok else "SELF-CHECK FAILED")
    return 0 if ok else 1


def _indent(text: str) -> str:
    return "\n".join("  " + line for line in text.splitlines())


if __name__ == "__main__":
    raise SystemExit(main())
