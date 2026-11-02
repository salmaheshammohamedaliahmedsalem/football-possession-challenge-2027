"""Prepare the three competition deliverables without committing licensed data."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


def safe_name(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9_.-]+", "_", value.strip())
    value = value.strip("._-")
    if not value:
        raise ValueError("team name must contain at least one filename-safe character")
    return value


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument("--team-name", required=True, help="exact registration team name, used for filenames")
    parser.add_argument("--candidate", required=True, type=Path, help="local generated possession CSV")
    parser.add_argument("--validator", required=True, type=Path, help="organisers' validate_submission.py")
    parser.add_argument("--out", type=Path, default=root / "submission_ready")
    args = parser.parse_args()

    candidate = args.candidate.expanduser().resolve()
    validator = args.validator.expanduser().resolve()
    if not candidate.is_file():
        parser.error(f"candidate does not exist: {candidate}")
    if not validator.is_file():
        parser.error(f"validator does not exist: {validator}")

    result = subprocess.run(
        [sys.executable, str(validator), str(candidate)],
        check=False,
        text=True,
        capture_output=True,
    )
    print(result.stdout, end="")
    print(result.stderr, end="", file=sys.stderr)
    if result.returncode:
        raise SystemExit(result.returncode)

    stem = safe_name(args.team_name)
    output = args.out.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    csv_path = output / f"{stem}.csv"
    doc_path = output / f"{stem}.md"
    shutil.copyfile(candidate, csv_path)
    shutil.copyfile(root / "docs" / "technical_submission.md", doc_path)

    print(f"prepared CSV: {csv_path}")
    print(f"prepared technical document: {doc_path}")
    print("public repository URL: https://github.com/salmaheshammohamedaliahmedsalem/football-possession-challenge-2027")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
