# Collaboration guide

## One-time setup

\`\`\`bash
git clone https://github.com/<owner>/football-possession-challenge-2027.git
cd football-possession-challenge-2027
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
\`\`\`

Keep the licensed match bundle outside the repository and set \`MTAH_DATA_DIR\` locally. See [\`../data/README.md\`](../data/README.md).

## Branches

\`main\` is stable. Create a personal branch before editing:

\`\`\`bash
git switch main
git pull --ff-only origin main
git switch -c salma/exploration
\`\`\`

Use \`khadija/exploration\` or \`omar/exploration\` for the other teammates. Later branches can be more specific, such as \`salma/atd-schema-notes\`.

## Commit and pull request workflow

\`\`\`bash
git status
git add docs/ salma/
git commit -m "Document ATD exploration findings"
git push -u origin salma/exploration
\`\`\`

Open a pull request on GitHub into \`main\`. Explain what was inspected, include the reproducible command, and confirm that no licensed data or sensitive derived output is included. Another teammate reviews before merge.

## Avoiding conflicts

- Work primarily inside your own directory.
- Put shared decisions in \`docs/findings.md\`, one dated entry at a time.
- Do not edit another person's notebook or script without coordination.
- Pull \`main\` before starting new work.
- Never commit \`.mp4\`, raw ATD/XML, homography data, private labels, or frame-level generated outputs.

## Adding collaborators

The repository owner must add Khadija and Omar from GitHub's repository Settings → Collaborators. Their GitHub usernames are required; do not guess them.

