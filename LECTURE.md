# The lecture this repo implements

**Building Agents with the Claude Agent SDK — Anthropic workshop (Tariq, @TRQ212)**
≈1h52m · one of Anthropic's "build agents from scratch" workshop sessions.

Quotes below are verbatim from the auto-caption transcript, cleaned only of
stutters (the captioner mishears "Claude" as "Cloud"). Timestamps point at where
each line is spoken. Nothing is paraphrased.

---

## The claim the repo is built on

> **22:20** — "here is the three parts to an agent loop. So, first, it's gather
> context. Second is taking action, and the third is verifying the work."

Most "loop" content online shows the first two parts and drops the third. This
repo is the third part made load-bearing: a loop where **verify is a gate**, not
a step you tack on at the end.

> **23:36** — "if you can verify its work, it's a great candidate for an agent.
> If you can't verify its work..."

Verifiability is the selection criterion for what an agent should even attempt.
A table edit is verifiable (does the column exist? is the value non-null?), so
it is a clean domain to show the gate on.

> **68:05** — "the best form of verification is rule-based."

Not a model grading itself — deterministic rules. `src/verifier.py` is exactly
that: rules that either hold or return a reason.

---

## Map: lecture → file

| MM:SS | what he says | where it lives here |
|---|---|---|
| 22:20 | three parts: gather, act, **verify** | `src/loop.py::run_loop` — the loop is literally those three, verify wired as a gate |
| 23:36 | agent-worthy iff you can **verify** its work | `src/verifier.py` — the whole task is chosen to be rule-verifiable |
| 68:05 | best verification is **rule-based** | `src/verifier.py` — deterministic rules, not an LLM judge |
| 68:07 | "if they're like a **null pointer**..." | the null-value rule (`refusing to write an empty/null value`) |
| 68:22 (read-before-write bug in Claude Code) | writing a column before reading it | `ReadColumn` gather + the read-before-write rule |
| 70:00 | in production you can't just "fix it" — state matters | `src/table.py` checkpoint/rollback; the demo undoes the destructive delete |
| 82:10 | "put [verification] in as many places as you can" | every op — gather included — passes through the same `verify()` gate |

---

## What you see when you run it

`./run.sh` runs a scripted, offline agent against `data/sales.csv`. Three of its
proposed operations are the exact mistakes the workshop names, and each is
blocked before it can touch the table:

```
step 1: REJECT SetCell(column='revenue')     -> column does not exist
step 3: REJECT SetCell(column='margin')       -> write before reading it
step 5: REJECT SetCell(value='   ')           -> empty/null value
...
rows: 4 -> 2 (after delete) -> 4 (after rollback)
```

The rollback line is the 70:00 point: the destructive delete was reversible only
because the loop checkpointed before applying it.

---

## What this repo deliberately does not claim

The workshop is careful that verification is easy for code and hard for open
domains (deep research verifies only by citing sources). So is this repo: it only
demonstrates the gate where a **real rule exists**. It is not a claim that every
agent task can be gated this cleanly — only that, where it can, the loop should.
