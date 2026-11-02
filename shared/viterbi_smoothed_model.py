"""Viterbi possession model with conservative spell consolidation.

The Viterbi decoder has strong frame-level accuracy but can split one live spell into
several short spells when the ball is absent.  This wrapper keeps the decoder's
emissions and temporal prior, then repairs only physically plausible gaps:

* a dead-state gap is bridged only when the same team is on both sides;
* the raw ball is absent for the whole gap and no set-piece tag overlaps it;
* short same-label flickers are removed after bridging.

These rules are fixed from the frame rate and the challenge's ball-occlusion pattern;
they do not read the public ground-truth labels.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from gap_filled_model import (
    graded_mask,
    interpolate_short_gaps,
    load_tactical_context,
    load_tracking,
    team_geometry,
    write_submission,
)
from mtah_constants import AWAY, DEAD, HOME
from viterbi_model import emissions, viterbi_segment

MAX_INTERP_GAP = 12
MAX_LIVE_GAP_FRAMES = 100  # four seconds at 25 FPS
MIN_FLICKER_FRAMES = 12    # about half a second at 25 FPS
STATE_LABELS = {HOME: "H", AWAY: "A", DEAD: "D"}


def runs(values: np.ndarray):
    if not len(values):
        return
    starts = np.r_[0, np.flatnonzero(values[1:] != values[:-1]) + 1]
    stops = np.r_[starts[1:], len(values)]
    for start, stop in zip(starts, stops):
        yield int(start), int(stop), int(values[start])


def consolidate(
    states: np.ndarray,
    raw_ball_x: np.ndarray,
    raw_ball_y: np.ndarray,
    set_piece: np.ndarray,
    graded: np.ndarray,
) -> tuple[np.ndarray, int, int]:
    """Consolidate only same-team, non-set-piece missing-ball gaps."""
    out = states.copy()
    bridged = 0
    for start, stop, code in list(runs(out)):
        if code != DEAD or start == 0 or stop >= len(out):
            continue
        if stop - start > MAX_LIVE_GAP_FRAMES or not graded[start:stop].all():
            continue
        if np.isfinite(raw_ball_x[start:stop]).any() or np.isfinite(raw_ball_y[start:stop]).any():
            continue
        if set_piece[start:stop].any():
            continue
        left = int(out[start - 1])
        right = int(out[stop])
        if left in (HOME, AWAY) and left == right:
            out[start:stop] = left
            bridged += stop - start

    repaired = 0
    changed = True
    while changed:
        changed = False
        for start, stop, code in list(runs(out)):
            if code not in (HOME, AWAY, DEAD) or stop - start >= MIN_FLICKER_FRAMES:
                continue
            if start == 0 or stop >= len(out):
                continue
            left = int(out[start - 1])
            right = int(out[stop])
            if left == right and left in (HOME, AWAY, DEAD):
                out[start:stop] = left
                repaired += stop - start
                changed = True
                break
    return out, bridged, repaired


def generate(meta_path: str, raw_path: str, smart_path: str, output: str) -> dict:
    tracking = load_tracking(meta_path, raw_path)
    ball_x, interp_x = interpolate_short_gaps(tracking.ball_x, MAX_INTERP_GAP)
    ball_y, interp_y = interpolate_short_gaps(tracking.ball_y, MAX_INTERP_GAP)
    interpolation_mask = interp_x & interp_y
    team_min, _, _, _ = team_geometry(tracking, ball_x, ball_y)
    set_piece, restart_team = load_tactical_context(smart_path, len(ball_x))
    score = emissions(
        team_min,
        tracking.ball_x,
        tracking.ball_y,
        interpolation_mask,
        set_piece,
        restart_team,
    )
    graded = graded_mask(len(ball_x))
    states = np.full(len(ball_x), DEAD, dtype=np.int8)
    for start, stop in ((11185, 90652), (110808, 190198)):
        states[start:stop] = viterbi_segment(
            score[start:stop], set_piece[start:stop], restart_team[start:stop]
        )

    states, bridged, repaired = consolidate(
        states, tracking.ball_x, tracking.ball_y, set_piece, graded
    )
    labels = np.full(len(states), "X", dtype="<U1")
    for state, label in STATE_LABELS.items():
        labels[graded & (states == state)] = label
    write_submission(output, labels)
    return {
        "frames": int(len(labels)),
        "graded_frames": int(graded.sum()),
        "ball_observed_frames": int(np.isfinite(tracking.ball_x).sum()),
        "short_gap_interpolated_frames": int(interpolation_mask.sum()),
        "set_piece_frames": int(set_piece.sum()),
        "bridged_frames": int(bridged),
        "flicker_repaired_frames": int(repaired),
        "labels": {label: int((labels == label).sum()) for label in ("H", "A", "D", "X")},
        "output": output,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", default=os.environ.get("MTAH_DATA_DIR"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    if not args.data_dir:
        parser.error("--data-dir or MTAH_DATA_DIR is required")
    tactical = Path(args.data_dir) / "tactical"
    paths = {
        "meta": tactical / "BAR-ATH_tactical_atd.xml",
        "raw": tactical / "BAR-ATH_tactical_atd.txt",
        "smart": tactical / "BAR-ATH_tactical_smart_tagging.xml",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        parser.error("missing required files:\n  " + "\n  ".join(missing))
    print(json.dumps(generate(str(paths["meta"]), str(paths["raw"]), str(paths["smart"]), args.out), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
