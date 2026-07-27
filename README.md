# Claude Token Diet

One paste into your Claude Code chat. It audits what your setup silently loads into every conversation, finds the bloat, and with your approval moves it out safely. Typical result: **thousands of tokens saved on every single session**, with zero information lost.

*Unofficial community tool, not affiliated with Anthropic.*

## The story (why this exists)

It started with an idea: what if you invented a compressed language for talking to Claude to save tokens? We tested that idea properly, same task, 15 runs per style, real token counts from the Claude Code CLI:

| Style | Context per call | Output per call | Cost per call |
|---|---|---|---|
| Verbose English | 8,129 | 346 | baseline |
| Terse English | 8,051 | 294 | cheapest |
| Invented shorthand + decoder | 8,376 | **632** | **+57%** |

The invented language **lost on both sides**. The decoder dictionary it needs in memory costs more than the short messages save, and the model roughly **doubles its output** working to decode the notation. Meanwhile, what you type is a rounding error (roughly 10 to 100 tokens) next to what Claude *carries* (8,000+ tokens of always-loaded context, re-read every turn).

The real lever, measured: **every KB of always-loaded CLAUDE.md costs 250 to 300 tokens per session start**, and again on every turn via cache reads. The most common bloat is a session log that quietly grew inside CLAUDE.md. Trimming one real 50 KB file to 12 KB saved a measured **11,760 tokens per session**, roughly 100x more than message compression could ever save.

This kit applies that fix to *your* setup.

## Use it (two ways)

**Option A, one-time paste:** open [`TOKEN-DIET-PROMPT.md`](TOKEN-DIET-PROMPT.md), copy the whole thing, paste it into a Claude Code chat in the project you want slimmed.

**Option B, install as a slash command (recommended):** copy [`commands/token-diet.md`](commands/token-diet.md) into your `~/.claude/commands/` folder (create it if needed). From then on, type `/token-diet` in any project, any time.

Either way, Claude will:
1. **Inventory** (read-only) every always-loaded file and show you the cost table.
2. **Propose** moving log-like content out verbatim, with projected savings, then **stop for your approval, file by file**.
3. **Apply** only what you approved: backup first, verbatim move, one-line-per-entry index left behind, self-verification, before and after report.

If your setup is already lean (under 8 KB total), it tells you so and changes nothing.

## Safety design

- Read-only until you explicitly approve, per file.
- A dated backup of every file before it's touched.
- Content is **moved, never deleted**. Full narratives live on in `docs/`, findable on demand.
- Self-check after the move: every entry must appear character-for-character in the new location, everything else must be unchanged, or it restores the backup.
- Never touches `.env`, credentials, or secrets.

## Honest caveats

- The 250 to 300 tokens/KB figure and the tables above were measured on 2026-07-09 against Claude Code v2.1.205 with claude-haiku-4-5, on one account. Treat them as directional, not gospel. Your absolute numbers will differ. The *shape* of the result won't.
- Savings show up as fewer tokens burned per session. On subscription plans that means more headroom before rate limits, not a smaller bill.
- After the diet, keep the habit: new session notes get **one line** in CLAUDE.md, full detail in the docs log. The kit leaves a pointer line behind so future sessions keep the pattern automatically.

## What's in this folder

- `TOKEN-DIET-PROMPT.md`, the paste-into-chat version (the product, same text as the command)
- `commands/token-diet.md`, the slash-command version for permanent install
- `tests/`, the harness used to prove the kit works. It generates a synthetic bloated project, runs the prompt against it headlessly with a fresh Claude, and mechanically verifies the result (backup exists, every entry moved verbatim, durable content untouched, secrets file untouched)
- `TESTING.md`, the full test matrix and the failure story that shaped the prompt (a model retyping long text mutates single words, caught twice, engineered out)
- `LICENSE`, MIT
