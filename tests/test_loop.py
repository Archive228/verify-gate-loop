"""Tests for the gate and the loop — not for any generated content.

What must be trustworthy: the verifier rejects the right things, the loop never
mutates on a rejection, and a checkpoint really restores state.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.loop import run_loop
from src.operations import AddColumn, DeleteRows, ReadColumn, SetCell
from src.scripted_agent import ScriptedAgent
from src.table import Table
from src.verifier import ROW_CAP, verify


def small_table() -> Table:
    return Table(columns=["region", "units"], rows=[{"region": "EU", "units": "1"}, {"region": "US", "units": "2"}])


class TestVerifier(unittest.TestCase):
    def test_setcell_unknown_column_rejected(self):
        t = small_table()
        self.assertFalse(verify(SetCell(0, "nope", "x"), t, {"nope"}))

    def test_setcell_before_read_rejected(self):
        t = small_table()
        self.assertFalse(verify(SetCell(0, "units", "9"), t, set()))

    def test_setcell_after_read_ok(self):
        t = small_table()
        self.assertTrue(verify(SetCell(0, "units", "9"), t, {"units"}))

    def test_null_value_rejected(self):
        t = small_table()
        self.assertFalse(verify(SetCell(0, "units", "   "), t, {"units"}))

    def test_row_out_of_range_rejected(self):
        t = small_table()
        self.assertFalse(verify(SetCell(5, "units", "9"), t, {"units"}))

    def test_addcolumn_duplicate_rejected(self):
        t = small_table()
        self.assertFalse(verify(AddColumn("units"), t, set()))

    def test_read_missing_column_rejected(self):
        t = small_table()
        self.assertFalse(verify(ReadColumn("ghost"), t, set()))

    def test_oversized_table_blocks_mutation(self):
        t = Table(columns=["a"], rows=[{"a": str(i)} for i in range(ROW_CAP + 1)])
        self.assertFalse(verify(SetCell(0, "a", "x"), t, {"a"}))


class TestLoop(unittest.TestCase):
    def test_rejection_never_mutates(self):
        t = small_table()
        before = t.snapshot()
        # agent that only ever proposes an illegal write, then stops
        seq = [SetCell(0, "ghost", "x"), None]
        i = {"n": 0}

        def agent(_cols, _reason):
            op = seq[i["n"]]
            i["n"] += 1
            return op

        log = run_loop(t, agent)
        self.assertEqual(log.accepted, 0)
        self.assertEqual(log.rejected, 1)
        self.assertEqual(t.snapshot(), before)  # unchanged

    def test_checkpoint_rolls_back_destructive(self):
        t = small_table()
        t.checkpoint()
        t.rows = [r for r in t.rows if r["region"] != "EU"]
        self.assertEqual(len(t.rows), 1)
        t.rollback()
        self.assertEqual(len(t.rows), 2)

    def test_scripted_run_fires_every_rule(self):
        t = Table(
            columns=["region", "product", "units"],
            rows=[{"region": "EU", "product": "w", "units": "1"},
                  {"region": "US", "product": "w", "units": "2"}],
        )
        log = run_loop(t, ScriptedAgent())
        reasons = " ".join(log.reject_reasons)
        self.assertEqual(log.rejected, 3)
        self.assertIn("does not exist", reasons)
        self.assertIn("read-before-write", reasons)
        self.assertIn("empty/null", reasons)
        self.assertIn("margin", t.columns)  # the valid work still happened


if __name__ == "__main__":
    unittest.main(verbosity=2)
