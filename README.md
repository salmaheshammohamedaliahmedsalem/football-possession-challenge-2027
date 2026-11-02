# Football Possession Challenge 2027

Shared exploration workspace for Salma, Khadija, and Omar for [More Than a Hack 2027](https://github.com/metrica-sports/more-than-a-hack-2027).

This repository is the team's work area. The organisers' repository remains the source of truth for the challenge documentation, starter code, validator, evaluator, and public baseline. We do not modify or copy the organisers' repository here, and we never commit the licensed match data.

## Phase 1 status

We are currently doing exploration only. No model training, hand annotation, or final algorithm selection is part of this phase.

Phase 1 covers:

- understanding `spellF1`, `macroF1`, possession spells, abstention, and submission rules;
- inspecting the ATD TXT/XML, track-slot team mapping, missing observations, and frame alignment;
- inspecting homography and Smart Tagging formats;
- reproducing and understanding the official baseline and local evaluator;
- documenting findings and questions before implementation begins.

The checklist is in [`docs/exploration_plan.md`](docs/exploration_plan.md).

## Repository layout

```text
salma/       Salma's notebooks and scripts
khadija/     Khadija's notebooks and scripts
omar/        Omar's notebooks and scripts
shared/      Reusable material agreed by the team
docs/        Challenge notes, exploration plan, findings, and collaboration guide
data/        Local-data instructions only; match assets are ignored
```

## Official materials

- [Challenge repository](https://github.com/metrica-sports/more-than-a-hack-2027)
- [Challenge definition](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/CHALLENGE.md)
- [Data description](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/DATA.md)
- [Evaluation](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/EVALUATION.md)
- [Rules](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/RULES.md)
- [Submission contract](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/SUBMISSION.md)

## Local data

The match bundle is gated and must be downloaded through the competition registration process. Keep it outside this public repository when possible. If you use a local `data/` folder, the files are ignored by Git. See [`data/README.md`](data/README.md).

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

For collaboration commands, see [`docs/collaboration_guide.md`](docs/collaboration_guide.md).

## Team rule

Use each person's directory for independent exploration and a personal branch for changes. Keep `main` stable. Open a pull request before merging shared work.
