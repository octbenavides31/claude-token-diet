"""Mechanical pass/fail check after running the Token Diet prompt on a fake project.

Usage: python verify_result.py <target_dir>    (same dir given to make_fake_project.py)
Exit code 0 = all checks pass.
"""
import hashlib
import json
import sys
from pathlib import Path


def norm(s: str) -> str:
    return s.replace("\r\n", "\n")


def main():
    if len(sys.argv) != 2:
        sys.exit("usage: python verify_result.py <target_dir>")
    target = Path(sys.argv[1])
    proj = target / "project"
    man = json.loads((target / "manifest.json").read_text(encoding="utf-8"))

    results = []

    def check(name, ok, detail=""):
        results.append((name, bool(ok), detail))

    cm = proj / "CLAUDE.md"
    new = norm(cm.read_text(encoding="utf-8")) if cm.exists() else ""
    check("CLAUDE.md exists", cm.exists())
    check("CLAUDE.md under 10 KB",
          cm.exists() and cm.stat().st_size < 10_000,
          f"{cm.stat().st_size if cm.exists() else 0:,} bytes")

    backups = [p for p in proj.glob("CLAUDE*backup*") if p.is_file()]
    orig_text = norm(man["claude_md_text"]).strip()
    check("dated backup exists with identical content",
          any(norm(b.read_text(encoding="utf-8")).strip() == orig_text for b in backups),
          f"found: {[b.name for b in backups]}")

    log_files = [p for p in proj.rglob("*.md")
                 if p.name != "CLAUDE.md" and "backup" not in p.name.lower()]
    blob = "\n".join(norm(p.read_text(encoding="utf-8")) for p in log_files)
    missing = [i for i, e in enumerate(man["entries"]) if norm(e).strip() not in blob]
    check(f"all {len(man['entries'])} entry bodies verbatim in a log file",
          not missing, f"log files: {[p.name for p in log_files]}; missing entries: {missing}")

    check("durable section unchanged inside CLAUDE.md", norm(man["durable"]).strip() in new)

    idx_lines = [l for l in new.splitlines() if l.strip().startswith("- 2026-")]
    check("index: one dated line per entry (>= 20)", len(idx_lines) >= 20, f"{len(idx_lines)} lines")

    for rel, h in man["hashes"].items():
        p = proj / rel
        ok = p.exists() and hashlib.sha256(p.read_bytes()).hexdigest() == h
        check(f"untouched: {rel}", ok)

    all_ok = all(ok for _, ok, _ in results)
    for name, ok, detail in results:
        print(f"{'PASS' if ok else 'FAIL'}  {name}" + (f"  [{detail}]" if detail else ""))
    print("\nOVERALL:", "PASS" if all_ok else "FAIL")
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
