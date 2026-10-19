"""Clean transient workspace areas only (P5).

Never touches ``workspace/imports`` or ``workspace/review`` (keepable), nor
``datasets/``, ``data/`` or ``reports/``. Default scope cleans staging /
extracted / reports; ``rejected`` is only cleaned when explicitly requested
(audit trail).

Run::

    .venv/Scripts/python scripts/maintenance/clean_workspace.py --dry-run
    .venv/Scripts/python scripts/maintenance/clean_workspace.py
    .venv/Scripts/python scripts/maintenance/clean_workspace.py --scope rejected
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TRANSIENT = ("staging", "extracted", "reports", "rejected")
DEFAULT_SCOPES = ("staging", "extracted", "reports")
KEEP_SCOPES = ("imports", "review")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--scope", action="append", choices=TRANSIENT, default=None,
                        help="repeatable; default staging/extracted/reports")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    workspace = root / "workspace"
    scopes = tuple(args.scope) if args.scope else DEFAULT_SCOPES

    targets: list[Path] = []
    for name in scopes:
        scope_dir = workspace / name
        if not scope_dir.exists():
            continue
        for path in scope_dir.rglob("*"):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if not resolved.is_relative_to((workspace / name).resolve()):
                raise SystemExit(f"refusing to delete outside scope boundary: {path}")
            targets.append(path)
    targets.sort(key=lambda p: str(p))

    report = {
        "dry_run": args.dry_run,
        "scopes": list(scopes),
        "keep_untouched": ["imports", "review", "datasets", "data", "reports"],
        "deleted_files": [str(p.relative_to(root)) for p in targets],
    }
    if not args.dry_run:
        for name in scopes:
            shutil.rmtree(workspace / name, ignore_errors=True)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
