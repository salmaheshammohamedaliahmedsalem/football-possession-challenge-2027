# Spain Lesgo — More than a Hack 2027 Phase 1

## Approach

The submission is a deterministic tracking-first possession classifier. It reads
the supplied tactical automatic tracking, Smart Tagging intervals, and the
provided frame alignment. For each frame it compares the nearest visible home
and away players to the ball in pitch coordinates. It then applies temporal
majority smoothing, conservative missing-ball gap bridging, and short-flicker
repair. A gap is bridged only when the same live team is present immediately on
both sides, the ball is absent throughout the gap, and no set-piece interval
overlaps it.

Two additional reproducible candidates are included in the public repository:
an energy/Viterbi decoder with explicit H/A/D persistence costs, and a smoothed
version that consolidates physically plausible missing-ball gaps. The final CSV
should be selected from these candidates after validation; the current primary
candidate is the gap-bridge output because the competition ranks spellF1 first.

## Assets used

The algorithm uses only the licensed competition bundle at runtime:

- tactical ATD XML/TXT tracking;
- tactical Smart Tagging XML;
- tactical frame alignment and pitch geometry as provided by the organisers.

The broadcast stream was inspected as a possible fallback. It was not used in
the current submission because its frame coverage and coordinate representation
do not provide a verified one-to-one replacement for the tactical stream.

## Training data

No labelled training data was used. The provided match was not hand-labelled,
and its public five-minute ground truth was used only to verify file format,
frame alignment, and end-to-end evaluator execution—not for training or tuning.
No private ground truth or human-produced data about the match was used.

## Possession rules

- `H` means Barcelona/home is in live possession.
- `A` means Athletic Club/away is in live possession.
- `D` means the ball is dead or no live team can be assigned reliably.
- `X` is used outside the two graded video blocks.
- Loose or missing-ball frames are resolved by temporal evidence, not manual
  correction. Set-piece tags prevent the missing-ball bridge from inventing a
  live spell through a restart.

## Limitations and next step

The supplied tactical ball is absent on a substantial fraction of scored frames,
and player tracking can contain identity switches. Without the challenge videos,
the current system cannot add a raw-pixel ball detector or camera-aware visual
fallback. If the enrolled video files become available, the next reproducible
extension is to detect/track the ball in tactical frames, align those detections
using the provided homography, and use them only as an algorithmic fallback in
high-confidence tactical gaps.

## Reproduction

From this repository, with the licensed bundle stored outside Git:

```bash
export MTAH_DATA_DIR="/absolute/path/to/More Than A Hack 2027 - Initial Challenge - Dataset"
python shared/bridge_gap_model.py --out /absolute/path/to/local-results/gap_filled_bridge.csv
python /absolute/path/to/more-than-a-hack-2027/evaluation/validate_submission.py \
  /absolute/path/to/local-results/gap_filled_bridge.csv
```

The Viterbi candidates can be regenerated with `shared/viterbi_model.py` and
`shared/viterbi_smoothed_model.py`. The repository contains code and documents
only; the licensed data and generated frame-level CSVs are excluded.
