# Phase 1 exploration plan

Phase 1 is data and evaluation understanding only. We are not training models or choosing a final algorithm yet.

## Checklist

### A. Competition and evaluation

- [x] Read \`CHALLENGE.md\`, \`EVALUATION.md\`, \`RULES.md\`, \`SUBMISSION.md\`, \`DATA.md\`, and \`FAQ.md\`.
- [x] Record that \`spellF1\` ranks entries and \`macroF1\` breaks ties.
- [x] Understand temporal IoU matching, possession spells, fragmentation, transitions, and abstention behavior.
- [x] Record the exact 199,319-row submission contract and validator command.
- [x] Confirm that public labels are not a tuning or training set.

### B. ATD TXT/XML

- [ ] Locate the local tactical metadata and raw ATD files without copying them into the public repository.
- [ ] Document the raw line structure and frame counter convention.
- [ ] Confirm how the XML maps track slots to the two teams.
- [ ] Confirm that track slots are tracklets, not persistent player identities.
- [ ] Measure missingness for players and ball locally.
- [ ] Record how gaps, duplicate tracks, and identity switches appear.

### C. Frame alignment

- [ ] Verify tactical video frame count and FPS against the official constants.
- [ ] Verify the per-half tracking offsets; do not assume one offset applies to both halves.
- [ ] Verify the graded spans and halftime gap.
- [ ] Confirm that submission frame numbering is zero-based while the raw tracking counter has its own convention.

### D. Homography

- [ ] Inspect column names, matrix ordering, validity flag, and reprojection error.
- [ ] Confirm that tactical homography is the usable reference and broadcast homography is partial.
- [ ] Record the normalized pitch-coordinate convention.

### E. Smart Tagging

- [ ] Inspect XML structure, timestamps, codes, tag groups, and team values.
- [ ] Confirm that timestamps map to tactical frames at 25 FPS.
- [ ] Identify set-piece and transition tags as contextual evidence only.
- [ ] Record missing/\`N/A\` team tags and the fact that intervals are phases, not possession spells.

### F. Official baseline and evaluator

- [x] Run the supplied evaluator on the committed public baselines.
- [x] Record the public-window result as a pipeline check only; do not tune on it.
- [ ] Run the official baseline once the licensed data bundle is available locally.
- [ ] Validate a known-good submission and an intentionally malformed file to understand failure messages.

### G. Exploration outputs

- [ ] Each teammate records observations in their own README/notebooks.
- [ ] Put only non-sensitive summaries, schemas, plots that cannot reconstruct the match, and questions in Git.
- [ ] Resolve disagreements in \`docs/findings.md\` before Phase 2 implementation begins.

## Suggested exploration notebooks

The notebooks should inspect structure and aggregate diagnostics rather than create labels or tune a model:

1. \`01_repository_and_metrics.ipynb\`
2. \`02_atd_schema_and_missingness.ipynb\`
3. \`03_alignment_and_homography.ipynb\`
4. \`04_smart_tagging_schema.ipynb\`
5. \`05_baseline_and_validator.ipynb\`

Keep notebooks local if their outputs contain frame-level or video-derived information that could expose the licensed match.

## Phase 1 exit criteria

Phase 1 is complete when all checklist items that require only local data inspection are answered, the official baseline/evaluator workflow is reproducible, and the team can explain what each asset means without having trained or tuned a model.

