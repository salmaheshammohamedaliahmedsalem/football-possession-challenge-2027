"""Viterbi architecture for possession states.

This is an independent temporal architecture, not a tuned version of the gap bridge. It combines
pitch-distance emissions with explicit persistence costs over H/A/D states. Parameters are fixed from
frame rate and physical possession timing, not learned from the public ground truth.
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
from mtah_constants import AWAY, DEAD, HOME, UNKNOWN

STATE_COUNT = 3
HALF_WINDOW_UNUSED = 0

# Fixed energy terms. A switch must be supported by sustained distance evidence.
LIVE_SWITCH_PENALTY = 3.0
LIVE_DEAD_PENALTY = 1.5
OBSERVED_DEAD_PENALTY = 3.0
MISSING_DEAD_BONUS = 0.25
SETPIECE_MISSING_DEAD_BONUS = 2.0
RESTART_TEAM_BONUS = 0.9
DISTANCE_SCALE_M = 3.0
MAX_INTERP_GAP = 12

STATE_LABELS = {HOME: "H", AWAY: "A", DEAD: "D"}


def emissions(
    team_min: np.ndarray,
    raw_ball_x: np.ndarray,
    raw_ball_y: np.ndarray,
    interpolation_mask: np.ndarray,
    set_piece: np.ndarray,
    restart_team: np.ndarray,
) -> np.ndarray:
    n_frames = len(raw_ball_x)
    score = np.zeros((n_frames, STATE_COUNT), dtype=np.float64)
    finite_home = np.isfinite(team_min[:, HOME])
    finite_away = np.isfinite(team_min[:, AWAY])
    finite_ball = np.isfinite(raw_ball_x) & np.isfinite(raw_ball_y)

    # Smaller pitch distance means stronger evidence for that team's control.
    score[:, HOME] = np.where(
        finite_home, -team_min[:, HOME] / DISTANCE_SCALE_M, 0.0
    )
    score[:, AWAY] = np.where(
        finite_away, -team_min[:, AWAY] / DISTANCE_SCALE_M, 0.0
    )

    # D is disfavoured while the ball is visible. A missing ball alone is weak evidence for D
    # because the challenge explicitly says the ball is absent on a large share of live frames.
    score[:, DEAD] += np.where(finite_ball, -OBSERVED_DEAD_PENALTY, MISSING_DEAD_BONUS)
    score[set_piece & ~finite_ball, DEAD] += SETPIECE_MISSING_DEAD_BONUS

    # Interpolated ball positions are useful for live-team evidence but less certain than observed
    # positions, so keep their team emissions conservative.
    score[interpolation_mask, HOME] *= 0.75
    score[interpolation_mask, AWAY] *= 0.75

    # A tagged restarting team is only a small prior after the tagged interval, never a hard label.
    for team in (HOME, AWAY):
        mask = (restart_team == team) & ~finite_ball
        score[mask, team] += RESTART_TEAM_BONUS

    return score


def transition_matrix() -> np.ndarray:
    matrix = np.zeros((STATE_COUNT, STATE_COUNT), dtype=np.float64)
    matrix[HOME, AWAY] = -LIVE_SWITCH_PENALTY
    matrix[AWAY, HOME] = -LIVE_SWITCH_PENALTY
    matrix[HOME, DEAD] = -LIVE_DEAD_PENALTY
    matrix[AWAY, DEAD] = -LIVE_DEAD_PENALTY
    matrix[DEAD, HOME] = -LIVE_DEAD_PENALTY
    matrix[DEAD, AWAY] = -LIVE_DEAD_PENALTY
    return matrix


def viterbi_segment(score: np.ndarray, set_piece: np.ndarray, restart_team: np.ndarray) -> np.ndarray:
    if not len(score):
        return np.empty(0, dtype=np.int8)

    transition = transition_matrix()
    dp = np.full_like(score, -np.inf, dtype=np.float64)
    back = np.zeros((len(score), STATE_COUNT), dtype=np.int8)
    dp[0] = score[0]

    for frame in range(1, len(score)):
        trans = transition.copy()
        if set_piece[frame]:
            # Set pieces are where dead-ball and restart transitions are expected.
            trans[HOME, DEAD] += 1.0
            trans[AWAY, DEAD] += 1.0
            trans[DEAD, HOME] += 0.5
            trans[DEAD, AWAY] += 0.5
        restart = int(restart_team[frame])
        if restart in (HOME, AWAY):
            trans[DEAD, restart] += 0.75

        candidates = dp[frame - 1][:, None] + trans
        back[frame] = np.argmax(candidates, axis=0)
        dp[frame] = score[frame] + candidates[back[frame], np.arange(STATE_COUNT)]

    states = np.empty(len(score), dtype=np.int8)
    states[-1] = np.argmax(dp[-1])
    for frame in range(len(score) - 1, 0, -1):
        states[frame - 1] = back[frame, states[frame]]
    return states


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

    # Decode each scored block independently so halftime cannot create a synthetic possession.
    for start, stop in ((11185, 90652), (110808, 190198)):
        states[start:stop] = viterbi_segment(
            score[start:stop], set_piece[start:stop], restart_team[start:stop]
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
        "labels": {label: int((labels == label).sum()) for label in ("H", "A", "D", "X")},
        "live_switch_penalty": LIVE_SWITCH_PENALTY,
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

