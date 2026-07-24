"""A deterministic, offline agent — a fixed sequence of proposed operations.

No model, no key, no network. The sequence is chosen to make each rule fire:

  1. write to a column that doesn't exist    -> REJECT (column exists)
  2. add a 'margin' column                     -> APPLY
  3. write margin without reading it           -> REJECT (read-before-write)
  4. read margin                               -> APPLY  (gather)
  5. write an empty value into margin          -> REJECT (null-check)
  6. write a real value                        -> APPLY
  7. read + write the second row               -> APPLY
  8. delete the EU rows (destructive)          -> checkpoint, then APPLY

A real model-backed agent with the same call signature drops in unchanged; it
would read `last_reason` to repair its own mistakes. See README.
"""
from __future__ import annotations

from typing import List, Optional

from .operations import AddColumn, DeleteRows, Operation, ReadColumn, SetCell


class ScriptedAgent:
    def __init__(self) -> None:
        self._plan: List[Optional[Operation]] = [
            SetCell(row=0, column="revenue", value="1200"),   # 1: no such column
            AddColumn(column="margin", default="0"),          # 2: create it
            SetCell(row=0, column="margin", value="0.4"),     # 3: not read yet
            ReadColumn(column="margin"),                      # 4: gather it
            SetCell(row=0, column="margin", value="   "),     # 5: empty/null
            SetCell(row=0, column="margin", value="0.4"),     # 6: valid
            SetCell(row=1, column="margin", value="0.35"),    # 7: valid (already read)
            DeleteRows(where_column="region", equals="EU"),   # 8: destructive
            None,                                             # done
        ]
        self._i = 0

    def __call__(self, columns: List[str], last_reason: Optional[str]) -> Optional[Operation]:
        op = self._plan[self._i]
        self._i += 1
        return op
