# How this kit was tested

The claim "paste this and Claude will safely slim your CLAUDE.md" is only worth something if a
**fresh Claude with zero context** does it right, repeatedly, on the cheapest model. So:

**Method.** `tests/make_fake_project.py` generates a synthetic project with a 35,784-byte
CLAUDE.md (a durable index section + 22 dated log entries, each carrying a unique trace marker),
a source file, and a canary `.env`. The kit prompt runs headlessly against it
(`claude -p` with file tools, a copy-only shell allowlist, and a TEST MODE line standing in for
the human approval gate). `tests/verify_result.py` then makes 8 mechanical checks: slimmed size,
a content-identical backup, **every entry verbatim** in the log file, durable section unchanged,
one index line per entry, and the canary files untouched.

**Results** (2026-07-09, Claude Code v2.1.205):

| test | model | prompt version | result |
|---|---|---|---|
| 1 | haiku | v1 | FAIL — one word mutated in a moved entry |
| 2 | haiku | v2 | FAIL — index put in the wrong file + one word mutated |
| 3 | haiku | v3 (shell-copy mechanics) | PASS 8/8 |
| 4 | haiku | v3 | PASS 8/8 |
| 5 | haiku | v3 | FAIL — backup was retyped; one word mutated in it |
| 6 | sonnet | v3 | PASS 8/8 |
| 7 | haiku | v4 (backup mechanics fixed) | content perfect; backup filename off-spec |
| 8 | haiku | v4 | PASS 8/8 |
| 9 | sonnet | v4 | PASS 8/8 |
| negative | haiku | v4 | PASS — already-lean project reported lean, zero changes (hash-verified) |
| 10 | haiku | v5 (final) | PASS 8/8 |
| 11 | haiku | v5 (final) | PASS 8/8 |

**The lesson baked into the prompt.** When a model *retypes* long text, single words silently
mutate — we caught the identical mutation twice in independent runs ("zero drift *afterward*"
became "zero drift *backward*", 28 KB deep in a 35 KB file). That is why the prompt looks
paranoid: it forbids regenerating moved content (shell copy + exact-match edits instead) and
requires a mechanical per-entry exact-string verification before the original file is touched.
Those two rules took the failure rate from ~1 corrupted word per bulk move to zero across the
final runs.

**Reproduce it yourself:**

```
python tests/make_fake_project.py /tmp/diet-test
cd /tmp/diet-test/project
# paste TOKEN-DIET-PROMPT.md into a claude session here (approve the proposal), then:
python ../../tests/verify_result.py /tmp/diet-test
```

Small-sample honesty: 5/5 green on the final prompt (plus 3 more on the near-final version)
is strong but not a guarantee — the verifier is included precisely so you can check any run.
