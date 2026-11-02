# Findings log

This is the shared, non-sensitive record of Phase 1 observations. Do not paste raw tracking rows, video frames, private labels, or derived data that could reconstruct the match.

## Initial findings from the official repository

- The task is frame-level possession labeling for 199,319 tactical-video frames.
- The ranked objective is complete possession recovery (\`spellF1\`), not ordinary frame accuracy.
- The baseline demonstrates that smoothing can improve possession-spell quality while changing \`macroF1\` in a different direction.
- Missing ball observations and noisy, identity-switching track slots are expected inputs.
- Smart Tagging is automatically inferred and should be treated as a noisy prior.
- The tactical stream is the submission index; the broadcast stream is not aligned automatically.
- The public five-minute labels contain too few possessions for reliable model selection.

## Local data audit

Pending licensed bundle access. Each teammate should add dated, aggregate observations here after review, for example:

\`\`\`text
### YYYY-MM-DD — name
- Asset inspected:
- Aggregate observation:
- Reproducible command/notebook:
- Open question:
\`\`\`

## Decisions

No modeling or final approach decisions have been made during Phase 1.

