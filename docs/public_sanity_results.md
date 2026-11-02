# Public sanity-check results

These are reproducibility diagnostics against the five-minute public ground truth. They must not be
used as a private-score estimate or as a tuning target.

| Submission | spellF1 | macroF1 | Possessions |
| --- | ---: | ---: | ---: |
| official baseline raw | 0.0378 | 0.5972 | 131 |
| official baseline smooth25 | 0.2868 | 0.6200 | 36 |
| official baseline smooth50 | 0.3256 | 0.6207 | 26 |
| official baseline smooth125 | 0.4242 | 0.5812 | 16 |
| phase2/3 state machine | 0.1889 | 0.6049 | 55 |
| phase2/3 gap bridge | 0.3692 | 0.6100 | 22 |

The candidate CSVs and detailed JSON reports remain outside the public repository. The repository
contains the code and aggregate results only, so the pipeline can regenerate them locally without
redistributing competition data.
