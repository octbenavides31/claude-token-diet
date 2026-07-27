# Claude Code Token Diet

Audit my always-loaded context and safely slim it. Background you should trust: every KB in an
always-loaded file (CLAUDE.md, CLAUDE.local.md, a memory index) costs roughly 250–300 tokens at
every session start and is re-read on every turn of the conversation. The most common bloat is
a session log that grew inside CLAUDE.md. Moving it out — verbatim, with an index left behind —
saves thousands of tokens per session with zero information loss.

Follow these steps exactly, in order.

## Step 1 — Inventory (read-only, change nothing)

Locate every always-loaded file that applies here:
- Project: `CLAUDE.md` and `CLAUDE.local.md` in the current directory and each parent directory
  up to the repo root.
- Global: the user-level `CLAUDE.md` (usually `~/.claude/CLAUDE.md`).
- Any auto-memory index file (e.g., `MEMORY.md`) if this setup has one.

Report a table, largest first: file | size in KB | estimated tokens per session (KB × 275) |
% log-like. "Log-like" means dated entries, session narratives, changelogs, "what we did" notes.
"Durable" means instructions, conventions, file maps, commands — things every session needs.

If the combined total is under 8 KB: say "Already lean — no changes needed," and stop here.

## Step 2 — Proposal (still change nothing)

For each file over 8 KB, or with more than ~30% log-like content:
- Propose moving the log-like sections VERBATIM into an on-demand file: `docs/<filename>-log.md`
  for project files (create `docs/` if needed), or a sibling `archive-log.md` for the global file.
- In its place — in the SAME always-loaded file, never in the log file — propose an index
  section: exactly one line per moved entry, in original order, each formatted exactly like
  `- 2026-05-02 — what happened, distilled to the durable outcome (max ~130 chars)` — plain
  hyphen bullet, date, dash, summary; no bold, no nesting. After the index, one pointer line
  so future sessions keep the pattern (new sessions add one line to this index, full narrative
  to the log file). The log file receives ONLY the moved entries, nothing else.
- Show projected new sizes and the estimated tokens saved per session.

Then stop and ask the user to approve, file by file. Do not edit anything without approval.

## Step 3 — Apply (only what was approved)

The one thing that must never happen here is silent mutation of moved text. Retyping long
content from memory is how single words quietly change — so do not retype it. Mechanics:

1. Backup first: duplicate the original to `<file>.backup-<YYYY-MM-DD>` — the original filename
   plus a dated suffix, e.g. `CLAUDE.md.backup-2026-07-09` — with a shell copy command
   (`cp` / `Copy-Item`) — a mechanical copy cannot mutate. Only if no shell
   is available may you write the backup manually, and then you must verify it with the same
   mechanical check as step 4 (exact string search of every entry's final sentence, run against
   the backup file) and fix any miss before going on.
2. Create the log file WITHOUT regenerating its content: prefer shell-copying the original
   file to the log location and then deleting the durable sections from the copy with
   exact-match edits. If no shell is available, build it in pieces copied directly from what
   you just read — then run the verification in step 4 before touching the original file.
3. Only after the log file passes verification: replace the log section in the original file
   with the index section exactly as proposed.
4. Verification (mandatory, mechanical — not a skim): for EVERY moved entry, take its final
   sentence and search for it verbatim in the new log file with an exact string search. Any
   miss means that entry mutated — fix it from the source before proceeding. Also confirm the
   durable sections are character-for-character unchanged. If verification cannot be made to
   pass, restore the backup and report what happened instead of pushing on.
5. Report before/after sizes and the total estimated tokens saved per session start.

## Hard rules

- Never delete content anywhere — only move it. Never touch `.env`, credentials, or any file
  containing secrets. Use absolute dates (like 2026-07-09), never "today".
- Do not add new rules or sections to any CLAUDE.md beyond the index + pointer — that would
  spend the very tokens this is saving.
- Files that are already lean indexes: leave them untouched and say so.
- Entries may look repetitive or near-duplicated — copy each one exactly as written anyway;
  never merge, dedupe, or "fix" text you are moving.
- If a section is ambiguous (half log, half instructions), ask instead of guessing.

## Closing report (plain English)

1. Total estimated tokens saved per session start.
2. The two habits that keep it lean:
   - Treat every CLAUDE.md as an index, not a log: new session notes get one line here, full
     detail in the docs log file.
   - Type requests in terse plain English. Do NOT invent shorthand codes: measured head-to-head,
     an invented code language plus its decoder dictionary costs MORE context than it saves and
     roughly doubles output tokens, because the model burns effort decoding it.
