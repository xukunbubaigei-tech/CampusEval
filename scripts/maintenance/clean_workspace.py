"""Clean explicitly selected workspace areas.

Never touches ``workspace/imports`` or ``workspace/review`` (keepable), nor
``datasets/``, ``data/`` or ``reports/``. The default only cleans staging.
Extraction sources, maintenance records and rejected imports are retained
unless their scope is explicitly selected.

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
CLEANABLE_SCOPES = ("staging", "extracted", "reports", "rejected")
DEFAULT_SCOPES = ("staging",)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=ROOT)
    parser.add_argument("--scope", action="append", choices=CLEANABLE_SCOPES, default=None,
                        help="repeatable; default staging only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    root = args.project_root.resolve()
    workspace = (root / "workspace").resolve()
    if workspace != root / "workspace":
        raise SystemExit(f"workspace resolves outside intended directory: {workspace}")
    scopes = tuple(dict.fromkeys(args.scope or DEFAULT_SCOPES))

    targets: list[Path] = []
    scope_dirs: list[Path] = []
    for name in scopes:
        scope_dir = (workspace / name).resolve()
        if scope_dir.parent != workspace or scope_dir.name != name:
            raise SystemExit(f"scope resolves outside intended directory: {scope_dir}")
        if not scope_dir.exists():
            continue
        scope_dirs.append(scope_dir)
        for path in scope_dir.rglob("*"):
            resolved = path.resolve()
            if not resolved.is_relative_to(scope_dir):
                raise SystemExit(f"refusing to delete outside scope boundary: {path}")
            if path.is_file():
                targets.append(path)
    targets.sort(key=lambda p: str(p))

    report = {
        "dry_run": args.dry_run,
        "scopes": list(scopes),
        "keep_untouched": ["imports", "review", "datasets", "data", "reports"],
        "deleted_files": [p.relative_to(root).as_posix() for p in targets],
    }
    if not args.dry_run:
        for scope_dir in scope_dirs:
            shutil.rmtree(scope_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
