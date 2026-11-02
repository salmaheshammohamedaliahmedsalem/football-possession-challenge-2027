"""Gap-bridging candidate built on the official temporal baseline.

The model keeps the baseline's stable majority vote, then repairs only short gaps where:
  * the raw ball is missing throughout the gap;
  * no Smart Tagging set-piece interval overlaps the gap; and
  * the same live team is visible immediately on both sides.

This is intentionally conservative: it avoids turning a likely stoppage into a possession.

"""


from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import numpy as np

from gap_filled_model import (
    build_predictions,
    graded_mask,
    interpolate_short_gaps,
    load_tactical_context,
    load_tracking,
    team_geometry,
    write_submission,
)
from mtah_constants import AWAY, HOME, N_FRAMES, OUTSIDE

HALF_WINDOW = 50
MAX_BRIDGE_FRAMES = 250
MIN_FLICKER_FRAMES = 12
LABEL_FOR = {HOME: "H", AWAY: "A", 2: "D", OUTSIDE: "X"}


def majority_codes(codes: np.ndarray, half_window: int) -> np.ndarray:
    home = (codes == HOME).astype(np.int32)
    away = (codes == AWAY).astype(np.int32)
    home_cum = np.concatenate(([0], np.cumsum(home)))
    away_cum = np.concatenate(([0], np.cumsum(away)))
    idx = np.arange(len(codes))
    low = np.maximum(0, idx - half_window)
    high = np.minimum(len(codes), idx + half_window + 1)
    h = home_cum[high] - home_cum[low]
    a = away_cum[high] - away_cum[low]
    out = np.full(len(codes), 2, dtype=np.int8)
    seen = (h + a) > 0
    out[seen] = np.where(h[seen] >= a[seen], HOME, AWAY)
    return out


def runs(values: np.ndarray):
    if not len(values):
        return
    starts = np.r_[0, np.flatnonzero(values[1:] != values[:-1]) + 1]
    stops = np.r_[starts[1:], len(values)]
    for start, stop in zip(starts, stops):
        yield int(start), int(stop), int(values[start])


def bridge_agreeing_gaps(
    smoothed: np.ndarray,
    raw_ball_x: np.ndarray,
    raw_ball_y: np.ndarray,
    set_piece: np.ndarray,
    graded: np.ndarray,
) -> tuple[np.ndarray, int]:
    out = smoothed.copy()
    bridged = 0
    for start, stop, code in runs(out):
        if code != 2 or start == 0 or stop >= len(out):
            continue
        if stop - start > MAX_BRIDGE_FRAMES:
            continue
        if not graded[start:stop].all():
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
    return out, bridged


def remove_short_flickers(values: np.ndarray, minimum: int) -> tuple[np.ndarray, int]:
    out = values.copy()
    repaired = 0
    changed = True
    while changed:
        changed = False
        for start, stop, code in list(runs(out)):
            if code not in (HOME, AWAY, 2) or stop - start >= minimum:
                continue
            if start == 0 or stop >= len(out):
                continue
            left = int(out[start - 1])
            right = int(out[stop])
            if left == right and left in (HOME, AWAY, 2):
                out[start:stop] = left
                repaired += stop - start
                changed = True
                break
    return out, repaired


def generate(meta_path: str, raw_path: str, smart_path: str, output: str) -> dict:
    tracking = load_tracking(meta_path, raw_path)
    ball_x, _ = interpolate_short_gaps(tracking.ball_x, 12)
    ball_y, _ = interpolate_short_gaps(tracking.ball_y, 12)
    _, nearest_team, _, _ = team_geometry(tracking, ball_x, ball_y)
    set_piece, _ = load_tactical_context(smart_path, len(ball_x))
    graded = graded_mask(len(ball_x))

    smoothed = majority_codes(nearest_team, HALF_WINDOW)
    bridged, bridged_frames = bridge_agreeing_gaps(
        smoothed, tracking.ball_x, tracking.ball_y, set_piece, graded
    )
    repaired, repaired_frames = remove_short_flickers(bridged, MIN_FLICKER_FRAMES)

    labels = np.array([LABEL_FOR.get(int(code), "D") for code in repaired], dtype="<U1")
    labels[~graded] = "X"
    write_submission(output, labels)

    summary = {
        "frames": int(len(labels)),
        "graded_frames": int(graded.sum()),
        "ball_observed_frames": int(np.isfinite(tracking.ball_x).sum()),
        "half_window": HALF_WINDOW,
        "max_bridge_frames": MAX_BRIDGE_FRAMES,
        "min_flicker_frames": MIN_FLICKER_FRAMES,
        "bridged_frames": int(bridged_frames),
        "flicker_repaired_frames": int(repaired_frames),
        "labels": {label: int((labels == label).sum()) for label in ("H", "A", "D", "X")},
        "output": output,
    }
    return summary


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
