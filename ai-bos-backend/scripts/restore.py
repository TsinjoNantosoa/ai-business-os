#!/usr/bin/env python3
"""CLI restore: python -m scripts.restore backup_YYYYMMDD_HHMMSS_xxxxxxxx [--no-storage]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.backup_service import restore_backup  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Restore AI BOS backup archive")
    parser.add_argument("backup_id", help="Backup id (stem of zip in BACKUP_DIR)")
    parser.add_argument("--no-storage", action="store_true")
    parser.add_argument("--yes", action="store_true", help="Skip interactive confirm")
    args = parser.parse_args()
    if not args.yes:
        answer = input(f'Type RESTORE to restore "{args.backup_id}": ').strip()
        if answer != "RESTORE":
            raise SystemExit("Aborted")
    result = restore_backup(args.backup_id, restore_storage=not args.no_storage)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
