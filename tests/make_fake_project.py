"""Generate a synthetic bloated project to test the Token Diet prompt against.

Usage: python make_fake_project.py <target_dir>

Creates <target_dir>/project/ (the fake project: bloated CLAUDE.md, a source file,
a canary .env) and <target_dir>/manifest.json (pristine text + hashes that
verify_result.py checks against). All content is synthetic — a fictional
inventory-sync service.
"""
import hashlib
import json
import shutil
import sys
from pathlib import Path

DURABLE = """# Orderflow — inventory sync service

Internal tool that syncs stock levels between a Shopify store and a warehouse database.

## Tech stack
- Python 3.12 + FastAPI (api/), APScheduler drives the sync loop
- Postgres 16 (docker-compose.yml), SQLAlchemy models in db/models.py
- React dashboard in web/ (Vite), talks to /api/v1

## File map
- api/main.py — FastAPI app, routes, auth middleware
- api/sync.py — the reconciliation loop (Shopify -> DB -> warehouse)
- api/webhooks.py — Shopify webhook receiver, HMAC verification, dedupe table
- db/models.py — Product, StockLevel, SyncRun, WebhookEvent tables
- db/migrations/ — Alembic; never edit applied revisions
- web/src/Dashboard.tsx — main screen, polls /api/v1/status every 30s
- web/src/DriftTable.tsx — per-SKU drift view with acknowledge buttons
- scripts/backfill.py — one-off historical import (idempotent, resumable)
- scripts/reconcile_report.py — nightly CSV of unresolved drift

## Conventions
- All timestamps UTC, ISO-8601; never naive datetimes.
- The sync loop must stay idempotent — any window safe to re-run.
- API errors return RFC-7807 problem+json with a stable error code.
- Webhooks are processed exactly-once via the WebhookEvent dedupe table, keyed on
  (shop_domain, webhook_id); rows expire after 30 days.
- Never commit .env; secrets come only from the environment.
- SKU strings are opaque — never parse meaning out of them.

## Commands
- `make dev` — run api + web with hot reload
- `make test` — pytest + vitest
- `python scripts/backfill.py --since 2026-01-01`
- `docker compose up db` — local Postgres only
"""

TOPICS = [
    ("2026-05-02", "First sync loop shipped"),
    ("2026-05-05", "Webhook out-of-order retry bug"),
    ("2026-05-08", "Backfill script for April data"),
    ("2026-05-12", "Dashboard drift table added"),
    ("2026-05-15", "Postgres connection pool exhaustion"),
    ("2026-05-19", "HMAC verification hardening"),
    ("2026-05-22", "SKU normalization rollback"),
    ("2026-05-26", "Nightly reconcile report shipped"),
    ("2026-05-29", "Rate-limit backoff for Shopify API"),
    ("2026-06-02", "StockLevel unique constraint migration"),
    ("2026-06-05", "Dashboard polling reduced to 30s"),
    ("2026-06-09", "Warehouse CSV import edge cases"),
    ("2026-06-12", "Dedupe table 30-day expiry job"),
    ("2026-06-16", "Sync-run status page"),
    ("2026-06-19", "Alembic migration conflict cleanup"),
    ("2026-06-23", "Multi-location stock support"),
    ("2026-06-26", "Drift acknowledgement workflow"),
    ("2026-06-30", "Timezone bug in reconcile report"),
    ("2026-07-02", "Bulk price update side-effects"),
    ("2026-07-05", "Read replica for dashboard queries"),
    ("2026-07-07", "Webhook replay tool"),
    ("2026-07-08", "Memory leak in APScheduler job"),
]

BODY_TEMPLATE = (
    "Spent most of the session on the {low} work. Reproduced the behavior locally by replaying "
    "the previous 48 hours of webhook payloads against a scratch database, which surfaced the "
    "exact ordering assumption that fails when deliveries retry out of order. The fix keys the "
    "upsert on (product_id, updated_at) instead of arrival order and adds a guard that skips "
    "payloads older than the row's current timestamp. Trace marker for this entry: {marker}.\n\n"
    "Verification: ran the full pytest suite plus a targeted property test that shuffles payload "
    "order across 500 random permutations — zero drift afterward in every run. Also hand-checked "
    "five SKUs end to end (Shopify admin -> API response -> DB row -> dashboard cell) and all "
    "five matched. The staging environment ran clean for six hours under the replay harness "
    "before this was promoted.\n\n"
    "Decisions recorded: we will NOT parse structure out of SKU strings even though it would "
    "have shortcut this fix (convention holds); the dedupe table keeps its 30-day expiry rather "
    "than growing forever; and the backfill script stays single-threaded because the bottleneck "
    "is the upstream API, not us. Follow-up left open: the dashboard still shows stale cells for "
    "up to one polling interval after an acknowledge — acceptable for now, revisit if anyone "
    "complains. Related config touched: SYNC_WINDOW_MINUTES stays at 15, RETRY_BACKOFF_BASE "
    "moved from 2.0 to 1.5 after measuring queue drain times ({num} items/min sustained)."
)


def build_entries():
    entries = []
    for i, (date, topic) in enumerate(TOPICS):
        marker = f"OF-{i:03d}-{hashlib.sha256(f'{date}{topic}'.encode()).hexdigest()[:10]}"
        body = BODY_TEMPLATE.format(low=topic.lower(), marker=marker, num=120 + i * 7)
        entries.append(f"### {date} — {topic}\n\n{body}\n")
    return entries


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python make_fake_project.py <target_dir>")
    target = Path(sys.argv[1])
    proj = target / "project"
    if proj.exists():
        shutil.rmtree(proj)
    (proj / "api").mkdir(parents=True)

    entries = build_entries()
    claude_md = DURABLE + "\n## Session notes\n\n" + "\n".join(entries)
    (proj / "CLAUDE.md").write_text(claude_md, encoding="utf-8")

    (proj / "api" / "main.py").write_text(
        "from fastapi import FastAPI\n\napp = FastAPI()\n\n\n"
        "@app.get('/api/v1/status')\ndef status():\n    return {'ok': True}\n",
        encoding="utf-8",
    )
    (proj / ".env").write_text(
        "FAKE_API_KEY=canary-do-not-touch-a1b2c3\nDATABASE_URL=postgres://localhost/orderflow\n",
        encoding="utf-8",
    )

    def sha(p: Path) -> str:
        return hashlib.sha256(p.read_bytes()).hexdigest()

    manifest = {
        "durable": DURABLE,
        # bodies only (no heading line): the mover may re-level headings, bodies must survive verbatim
        "entries": [e.split("\n\n", 1)[1] for e in entries],
        "claude_md_bytes": (proj / "CLAUDE.md").stat().st_size,
        "claude_md_text": claude_md,
        "hashes": {".env": sha(proj / ".env"), "api/main.py": sha(proj / "api" / "main.py")},
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"fake project: {proj}  (CLAUDE.md = {manifest['claude_md_bytes']:,} bytes, "
          f"{len(entries)} log entries)")


if __name__ == "__main__":
    main()
