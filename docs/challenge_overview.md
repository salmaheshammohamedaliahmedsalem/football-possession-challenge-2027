# Challenge overview

Source of truth: the [official organisers' repository](https://github.com/metrica-sports/more-than-a-hack-2027).

## Objective

For every frame of the 199,319-frame tactical recording, produce one label:

| Label | Meaning |
| --- | --- |
| \`H\` | Barcelona in possession, ball alive |
| \`A\` | Athletic Club in possession, ball alive |
| \`D\` | Dead ball |
| \`X\` | No answer / abstention |

The submission is indexed to the tactical video. The broadcast video is optional and has a separate, unsynchronised timeline.

## Metrics

- \`spellF1\` is the ranking metric. It matches complete \`H\`/\`A\` possession intervals by temporal IoU at five thresholds: 0.3, 0.4, 0.5, 0.6, and 0.7.
- \`macroF1\` is the frame-level mean F1 over \`H\`, \`A\`, and \`D\`, and is the first tie-break.
- Possession fragmentation is a central failure mode: a prediction can have respectable frame-level scores while inventing many short possessions.
- The public five-minute ground truth is for checking pipeline correctness, not training or tuning.

## Inputs to understand

1. ATD tracking metadata and raw tracking: team membership, track slots, positions, speeds, and ball observations.
2. Tactical homography: one matrix per tactical frame, with validity and reprojection error.
3. Smart Tagging XML: automatically inferred tactical intervals and set pieces; evidence, not ground truth.
4. Tactical and broadcast videos: the tactical recording is the frame-index authority; broadcast alignment is not provided.

## Hard constraints

- Exactly 199,319 output rows with \`frame,label\` and frame values \`0\` through \`199318\`.
- No hand labels or hand-corrected tracking for this match.
- No private ground truth or human-produced event data about this match.
- The public repository must regenerate the final CSV and must not contain licensed match data.
- The submission deadline is November 17, 2026.

