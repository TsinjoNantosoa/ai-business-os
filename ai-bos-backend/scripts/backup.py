#!/usr/bin/env python3
"""CLI backup: python -m scripts.backup [--no-storage]"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure backend root on path when run as script
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.services.backup_service import create_backup  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Create AI BOS backup archive")
    parser.add_argument("--no-storage", action="store_true", help="Skip local document storage")
    args = parser.parse_args()
    info = create_backup(include_storage=not args.no_storage)
    print(
        json.dumps(
            {
                "id": info.id,
                "path": info.path,
                "createdAt": info.created_at,
                "sizeBytes": info.size_bytes,
                "engine": info.engine,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
