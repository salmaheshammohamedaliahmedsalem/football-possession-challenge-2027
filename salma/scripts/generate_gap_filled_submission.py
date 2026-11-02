#!/usr/bin/env python3
"""Generate the Phase 2/3 tracking + temporal candidate."""

from pathlib import Path
import sys

HERE = Path(__file__).resolve()
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "shared"))

from gap_filled_model import main

if __name__ == "__main__":
    raise SystemExit(main())

