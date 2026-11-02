# Local competition data

The match assets are licensed and must not be committed to this public repository, redistributed, or uploaded to hosted/cloud LLMs. This directory contains instructions only.

## Recommended setup

Keep the downloaded bundle outside the repository and point the official starter code at it:

```bash
export MTAH_DATA_DIR="/absolute/path/to/mtah2027"
```

The expected bundle contains:

```text
mtah2027/
├── tactical/
│   ├── BAR-ATH_tactical.mp4
│   ├── BAR-ATH_tactical_atd.xml
│   ├── BAR-ATH_tactical_atd.txt
│   ├── BAR-ATH_tactical_homography.csv
│   └── BAR-ATH_tactical_smart_tagging.xml
└── broadcast/
    ├── BAR-ATH_broadcast.mp4
    ├── BAR-ATH_broadcast_atd.xml
    ├── BAR-ATH_broadcast_atd.txt
    └── BAR-ATH_broadcast_homography.csv
```

Do not commit raw files, derived tracking exports, clipped video, private ground truth, or any other artifact that could reconstruct the match.
