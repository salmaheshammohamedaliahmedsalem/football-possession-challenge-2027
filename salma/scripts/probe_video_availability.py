#!/usr/bin/env python3
"""Check whether optional tactical/broadcast video assets are available locally."""

from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", required=True)
    args = parser.parse_args()
    root = Path(args.data_dir)
    for source in ("tactical", "broadcast"):
        matches = sorted((root / source).glob("*.mp4"))
        print(f"{source}: {len(matches)} video file(s)")
        for path in matches:
            print(f"  {path} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

