"""Tracking-first possession model for Phase 2/3.

This model is deliberately deterministic and inspectable. It improves the official nearest-player
baseline by:
  * interpolating only short ball gaps;
  * comparing the closest player from each team in metres;
  * requiring persistent, good-quality evidence before changing possession;
  * using Smart Tagging set-piece intervals as context for dead-ball/restart frames;
  * respecting the two graded half-blocks and emitting X outside them.

It does not read the public ground truth and does not train on this match.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from mtah_constants import (
    AWAY,
    DEAD,
    FPS,
    GRADED_VIDEO_BLOCKS,
    HOME,
    N_FRAMES,
    OUTSIDE,
    PITCH_LENGTH_M,
    PITCH_WIDTH_M,
    UNKNOWN,
)

GROUP_SEP = ";"
FIELD_SEP = ":"
MISSING = "N"

MAX_INTERP_GAP = 12
SWITCH_CONFIRM_FRAMES = 8
MAX_CONTROL_DISTANCE_M = 5.0
MIN_TEAM_MARGIN_M = 0.35
RESTART_PRIOR_FRAMES = 50
LABEL_FOR_CODE = {HOME: "H", AWAY: "A", DEAD: "D", OUTSIDE: "X"}


@dataclass
class TrackingArrays:
    player_x: np.ndarray
    player_y: np.ndarray
    ball_x: np.ndarray
    ball_y: np.ndarray
    team_of_track: np.ndarray
    home_name: str
    away_name: str


def team_of_each_track(meta_path: str) -> tuple[np.ndarray, str, str]:
    root = ET.parse(meta_path).getroot()
    team_ids = [team.get("id") for team in root.iter("Team")]
    if len(team_ids) != 2:
        raise ValueError(f"{meta_path}: expected exactly two teams, found {len(team_ids)}")
    team_names = tuple(team.findtext("Name") or "" for team in root.iter("Team"))
    slots = [player.get("teamId") for player in root.iter("Player")]
    if not slots:
        raise ValueError(f"{meta_path}: no Player entries")
    home_id = team_ids[0]
    teams = np.array([HOME if team_id == home_id else AWAY for team_id in slots], dtype=np.int8)
    return teams, team_names[0], team_names[1]


def _parse_xy(group: str) -> tuple[float, float] | None:
    if not group or group[0] == MISSING:
        return None
    values = group.split(",", 2)
    if len(values) < 2:
        return None
    try:
        x, y = float(values[0]), float(values[1])
    except ValueError:
        return None
    if not (np.isfinite(x) and np.isfinite(y)):
        return None
    return x, y


def load_tracking(meta_path: str, raw_path: str, n_frames: int = N_FRAMES) -> TrackingArrays:
    teams, home_name, away_name = team_of_each_track(meta_path)
    n_tracks = len(teams)
    player_x = np.full((n_frames, n_tracks), np.nan, dtype=np.float32)
    player_y = np.full((n_frames, n_tracks), np.nan, dtype=np.float32)
    ball_x = np.full(n_frames, np.nan, dtype=np.float32)
    ball_y = np.full(n_frames, np.nan, dtype=np.float32)

    with open(raw_path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            parts = line.rstrip("\n").split(FIELD_SEP)
            if len(parts) != 3:
                continue
            try:
                frame = int(parts[0]) - 1
            except ValueError:
                continue
            if frame < 0 or frame >= n_frames:
                continue

            for slot, group in enumerate(parts[1].split(GROUP_SEP)[:n_tracks]):
                point = _parse_xy(group)
                if point is not None:
                    player_x[frame, slot] = point[0] * PITCH_LENGTH_M
                    player_y[frame, slot] = point[1] * PITCH_WIDTH_M

            point = _parse_xy(parts[2])
            if point is not None:
                ball_x[frame] = point[0] * PITCH_LENGTH_M
                ball_y[frame] = point[1] * PITCH_WIDTH_M

    return TrackingArrays(player_x, player_y, ball_x, ball_y, teams, home_name, away_name)


def graded_mask(n_frames: int = N_FRAMES) -> np.ndarray:
    mask = np.zeros(n_frames, dtype=bool)
    for start, stop in GRADED_VIDEO_BLOCKS:
        mask[start : stop + 1] = True
    return mask


def interpolate_short_gaps(values: np.ndarray, max_gap: int) -> tuple[np.ndarray, np.ndarray]:
    filled = values.astype(np.float32, copy=True)
    observed = np.isfinite(values)
    interpolated = np.zeros(len(values), dtype=bool)
    known = np.flatnonzero(observed)
    for left, right in zip(known[:-1], known[1:]):
        gap = right - left - 1
        if 0 < gap <= max_gap:
            filled[left : right + 1] = np.linspace(values[left], values[right], gap + 2)
            interpolated[left + 1 : right] = True
    return filled, interpolated


def team_geometry(
    tracking: TrackingArrays,
    ball_x: np.ndarray,
    ball_y: np.ndarray,
    chunk_size: int = 4096,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n_frames = len(ball_x)
    team_min = np.full((n_frames, 2), np.inf, dtype=np.float32)
    nearest_team = np.full(n_frames, UNKNOWN, dtype=np.int8)

    for start in range(0, n_frames, chunk_size):
        stop = min(n_frames, start + chunk_size)
        bx = ball_x[start:stop, None]
        by = ball_y[start:stop, None]
        valid_ball = np.isfinite(bx[:, 0]) & np.isfinite(by[:, 0])
        dx = tracking.player_x[start:stop] - bx
        dy = tracking.player_y[start:stop] - by
        distance = np.sqrt(dx * dx + dy * dy)
        distance[~np.isfinite(distance)] = np.inf

        for team in (HOME, AWAY):
            slots = np.flatnonzero(tracking.team_of_track == team)
            if len(slots):
                team_min[start:stop, team] = np.min(distance[:, slots], axis=1)

        nearest = np.argmin(team_min[start:stop], axis=1).astype(np.int8)
        nearest[~valid_ball | ~np.isfinite(np.min(team_min[start:stop], axis=1))] = UNKNOWN
        nearest_team[start:stop] = nearest

    margin = np.zeros(n_frames, dtype=np.float32)
    both_teams_visible = np.isfinite(team_min[:, HOME]) & np.isfinite(team_min[:, AWAY])
    margin[both_teams_visible] = np.abs(
        team_min[both_teams_visible, HOME] - team_min[both_teams_visible, AWAY]
    )
    nearest_distance = np.min(team_min, axis=1)
    return team_min, nearest_team, nearest_distance, margin


def _normalise_team(value: str | None) -> int:
    value = (value or "").strip().lower()
    if "barcelona" in value:
        return HOME
    if "athletic" in value or "atletic" in value:
        return AWAY
    return UNKNOWN


def load_tactical_context(path: str, n_frames: int = N_FRAMES) -> tuple[np.ndarray, np.ndarray]:
    set_piece = np.zeros(n_frames, dtype=bool)
    restart_team = np.full(n_frames, UNKNOWN, dtype=np.int8)
    root = ET.parse(path).getroot()

    for instance in root.iter("instance"):
        code = (instance.findtext("code") or "").strip().lower()
        try:
            start = int(round(float(instance.findtext("start")) * FPS))
            end = int(round(float(instance.findtext("end")) * FPS))
        except (TypeError, ValueError):
            continue
        start = max(0, min(n_frames, start))
        end = max(start, min(n_frames, end))
        tags = {
            label.findtext("group"): label.findtext("text")
            for label in instance.findall("label")
        }

        if code == "set pieces":
            set_piece[start:end] = True
            team = _normalise_team(tags.get("Team"))
            if team != UNKNOWN and end < n_frames:
                restart_team[end : min(n_frames, end + RESTART_PRIOR_FRAMES)] = team

    return set_piece, restart_team


def build_predictions(
    tracking: TrackingArrays,
    smart_tagging_path: str,
    switch_confirm_frames: int = SWITCH_CONFIRM_FRAMES,
    max_interp_gap: int = MAX_INTERP_GAP,
) -> tuple[np.ndarray, dict]:
    ball_x, ball_x_interp = interpolate_short_gaps(tracking.ball_x, max_interp_gap)
    ball_y, ball_y_interp = interpolate_short_gaps(tracking.ball_y, max_interp_gap)
    interpolation_mask = ball_x_interp & ball_y_interp
    ball_available = np.isfinite(ball_x) & np.isfinite(ball_y)

    _, nearest_team, nearest_distance, margin = team_geometry(tracking, ball_x, ball_y)
    set_piece, restart_team = load_tactical_context(smart_tagging_path, len(ball_x))
    graded = graded_mask(len(ball_x))

    quality = (
        (nearest_team != UNKNOWN)
        & np.isfinite(nearest_distance)
        & (nearest_distance <= MAX_CONTROL_DISTANCE_M)
        & (margin >= MIN_TEAM_MARGIN_M)
    )
    observed_quality = quality & ~interpolation_mask
    dead_hint = set_piece & ~ball_available

    output_codes = np.full(len(ball_x), OUTSIDE, dtype=np.int8)
    state = OUTSIDE
    pending_team = UNKNOWN
    pending_count = 0

    for frame in range(len(ball_x)):
        if not graded[frame]:
            state = OUTSIDE
            pending_team = UNKNOWN
            pending_count = 0
            continue

        candidate = int(nearest_team[frame])
        strong = bool(quality[frame])
        has_evidence = candidate in (HOME, AWAY)

        if dead_hint[frame] and not has_evidence:
            state = DEAD
            pending_team = UNKNOWN
            pending_count = 0
        elif has_evidence:
            if state in (OUTSIDE, DEAD):
                if strong or observed_quality[frame]:
                    state = candidate
                    pending_team = UNKNOWN
                    pending_count = 0
                elif restart_team[frame] in (HOME, AWAY):
                    state = int(restart_team[frame])
            elif candidate == state:
                pending_team = UNKNOWN
                pending_count = 0
            elif strong:
                if pending_team == candidate:
                    pending_count += 1
                else:
                    pending_team = candidate
                    pending_count = 1
                if pending_count >= switch_confirm_frames:
                    state = candidate
                    pending_team = UNKNOWN
                    pending_count = 0
            else:
                pending_team = UNKNOWN
                pending_count = 0
        elif state in (HOME, AWAY):
            pass
        elif restart_team[frame] in (HOME, AWAY):
            state = int(restart_team[frame])

        output_codes[frame] = state if state in (HOME, AWAY, DEAD) else DEAD

    labels = np.array([LABEL_FOR_CODE.get(int(code), "X") for code in output_codes], dtype="<U1")
    labels[~graded] = "X"

    summary = {
        "frames": int(len(labels)),
        "graded_frames": int(graded.sum()),
        "ball_observed_frames": int(np.isfinite(tracking.ball_x).sum()),
        "short_gap_interpolated_frames": int(interpolation_mask.sum()),
        "set_piece_frames": int(set_piece.sum()),
        "labels": {label: int((labels == label).sum()) for label in ("H", "A", "D", "X")},
        "switch_confirm_frames": int(switch_confirm_frames),
        "max_interp_gap": int(max_interp_gap),
        "home_team": tracking.home_name,
        "away_team": tracking.away_name,
    }
    return labels, summary


def write_submission(path: str | os.PathLike[str], labels: np.ndarray) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(("frame", "label"))
        writer.writerows((frame, label) for frame, label in enumerate(labels))


def run(meta_path: str, raw_path: str, smart_tagging_path: str, output_path: str) -> dict:
    tracking = load_tracking(meta_path, raw_path)
    labels, summary = build_predictions(tracking, smart_tagging_path)
    write_submission(output_path, labels)
    summary["output"] = str(output_path)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", default=os.environ.get("MTAH_DATA_DIR"))
    parser.add_argument("--out", required=True)
    args = parser.parse_args()

    if not args.data_dir:
        parser.error("--data-dir or MTAH_DATA_DIR is required")

    root = Path(args.data_dir)
    tactical = root / "tactical"
    paths = {
        "meta": tactical / "BAR-ATH_tactical_atd.xml",
        "raw": tactical / "BAR-ATH_tactical_atd.txt",
        "smart": tactical / "BAR-ATH_tactical_smart_tagging.xml",
    }
    missing = [str(path) for path in paths.values() if not path.is_file()]
    if missing:
        parser.error("missing required files:\n  " + "\n  ".join(missing))

    summary = run(str(paths["meta"]), str(paths["raw"]), str(paths["smart"]), args.out)
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
