# verify-gate-loop

![license MIT](https://img.shields.io/badge/license-MIT-green) ![python 3.9+](https://img.shields.io/badge/python-3.9+-blue) ![dependencies none](https://img.shields.io/badge/dependencies-none-brightgreen) ![tests 11 passing](https://img.shields.io/badge/tests-11%20passing-brightgreen) ![built from a lecture](https://img.shields.io/badge/built%20from-a%20lecture-8A2BE2)

**An agent loop where the third step — verify — is a gate, not an afterthought.**

`gather context → take action → verify the work`. Every proposed action is
checked by deterministic rules *before* it can touch the data. A rejection never
mutates anything; its reason is fed back as the next attempt's context. State is
checkpointed before anything destructive, so it can be rolled back.

Built from one line in Anthropic's Claude Agent SDK workshop:

> "here is the three parts to an agent loop. So, first, it's gather context.
> Second is taking action, and the third is **verifying the work**."
> — [22:20](https://www.youtube.com/watch?v=OZ9NhFwVCtQ&t=1340s)

Full timestamped map of lecture → code: [LECTURE.md](LECTURE.md).

---

## Run it

No install. No API key. No network.

```bash
git clone https://github.com/Archive228/verify-gate-loop
cd verify-gate-loop
./run.sh
```

```
step 1: REJECT SetCell(row=0, column='revenue', value='1200')
         -> column 'revenue' does not exist; columns are ['region', 'product', 'units']
step 2: APPLY  AddColumn(column='margin', default='0')
step 3: REJECT SetCell(row=0, column='margin', value='0.4')
         -> write to 'margin' before reading it (read-before-write)
step 4: READ   ReadColumn(column='margin')
step 5: REJECT SetCell(row=0, column='margin', value='   ')
         -> refusing to write an empty/null value
step 6: APPLY  SetCell(row=0, column='margin', value='0.4')
...
rollback demo: rows: 4 -> 2 (after delete) -> 4 (after rollback)
OK
```

Three rejections are the exact mistakes the workshop calls out (unknown column,
write-before-read, null value). None of them touched the table. The destructive
delete was reversible because the loop checkpointed first.

---

## The shape

```
agent ── proposes op ──► verify(op) ──► pass → apply (checkpoint first if destructive)
   ▲                                    fail → reason becomes the next prompt
   └──────────── last_reason ───────────────────┘
```

| file | what it is |
|---|---|
| `src/loop.py` | `run_loop()` — gather → act → verify; nothing mutates until verify passes |
| `src/verifier.py` | the rule-based gate: column-exists, read-before-write, null, row-cap |
| `src/table.py` | in-memory table with `checkpoint()` / `rollback()` |
| `src/operations.py` | `ReadColumn` / `SetCell` / `AddColumn` / `DeleteRows` as inspectable data |
| `src/scripted_agent.py` | offline deterministic agent (swap in a model — same signature) |

## Plug in a real model

The agent is just `(columns, last_reason) -> operation | None`. A model-backed
agent reads `last_reason` — the verifier's rejection text — and repairs its own
proposal, which is the whole point of returning failures as text:

```python
def claude_agent(columns, last_reason):
    prompt = f"Columns: {columns}. Propose the next table operation as JSON."
    if last_reason:
        prompt += f"\nYour last op was rejected: {last_reason}. Fix it."
    return parse(call_model(prompt))   # your call; must return an Operation
```

## Tests

```bash
python3 -m unittest discover -s tests -v   # 11 tests
```

They test the gate and the loop: rejections never mutate, every rule fires,
rollback restores state.

## Honest limits

- **Verification only works where a real rule exists.** Table edits, schemas,
  parsing, types. There is no rule here for "is this analysis any good" — the
  workshop says as much (deep research verifies only by citing sources).
- **The scripted agent is deterministic on purpose** — so the demo runs offline
  and always shows the same three rejections. Swap in a model for real work.

## License

MIT — see [LICENSE](LICENSE). All code here is original; nothing is vendored.

---

Built from a real lecture, quoted verbatim with timestamps in [LECTURE.md](LECTURE.md) — not a rehash of a rehash. If it made the idea click, ⭐ it.
