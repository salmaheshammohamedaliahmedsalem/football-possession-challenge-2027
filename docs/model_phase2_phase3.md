# Phase 2/3 model

## What was implemented

The candidate model in shared/gap_filled_model.py is a deterministic tracking-first system:

1. Parse the tactical ATD and preserve player/ball positions in metres.
2. Interpolate only short missing-ball gaps (up to 12 frames).
3. Compare the closest home and away player rather than only the single closest track.
4. Require a 0.35 m team-distance margin and a 5 m control-distance ceiling before accepting a possession switch.
5. Require 8 consecutive strong frames for a live H/A hand-over.
6. Use Smart Tagging set-piece intervals as context for dead-ball gaps and restart initialization.
7. Carry the last known live possession through longer missing-ball gaps rather than converting every missing ball to dead ball.
8. Emit X outside the two graded match blocks.

The parameters are fixed from the physical meaning of the data and the competition rules. They are not fitted to the public ground truth.

## Reproducibility

    export MTAH_DATA_DIR="/absolute/path/to/mtah2027"

    python salma/scripts/generate_gap_filled_submission.py \
      --out /absolute/path/to/local-results/gap_filled_temporal.csv

    python /path/to/more-than-a-hack-2027/evaluation/validate_submission.py \
      /absolute/path/to/local-results/gap_filled_temporal.csv

The output is intentionally kept outside Git because the competition data and derived frame-level predictions are restricted.

## Public sanity-check results

The generated files were validated with the organisers' validator and scored only against the
public five-minute ground truth. The public window is not a model-selection set, so these numbers
are recorded as diagnostics rather than a claim about the private competition score.

| Candidate | Public spellF1 | Public macroF1 | Predicted possessions |
| --- | ---: | ---: | ---: |
| Official smooth50 baseline | 0.3256 | 0.6207 | 26 |
| Initial state machine | 0.1889 | 0.6049 | 55 |
| Gap-bridging candidate | 0.3692 | 0.6100 | 22 |

The gap-bridging candidate is currently the strongest reproducible candidate. Its improvement is
structural: it preserves the official temporal smoothing behavior and bridges only short missing-ball
gaps with agreeing live-team evidence outside set-piece intervals.

## Computer vision status

The downloaded bundle contains no tactical or broadcast video files, so a raw-pixel model cannot be trained or evaluated from the available inputs. The homography and ATD are already computer-vision outputs, and this model uses their pitch geometry. salma/scripts/probe_video_availability.py is included so a future video bundle can be checked before adding an image model.
