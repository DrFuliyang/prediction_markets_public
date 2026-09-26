# GARCH extension for Prediction_Markets_Public

This branch is an academic extension of Diercks, Katz & Wright (2026),
*Kalshi and the Rise of Macro Markets*.

Upstream repository:
https://github.com/jdkatz21/Prediction_Markets_Public

## Purpose

The upstream project constructs daily probability distributions and moments from Kalshi.
This extension preserves those upstream objects and adds a meeting-frequency factor layer
for GARCH-MIDAS volatility research.

Primary factors:
- mean Kalshi variance over calendar days [-30,-3] before each FOMC statement;
- mean normalized Shannon entropy over the same fixed 28-day window;
- average daily trading volume in that window;
- day -28 snapshot robustness variables.

The [-30,-3] window is fixed ex ante because the audited 2022–2026 contract history gives
full range coverage for all 38 completed FOMC meetings through September 2026, while a
[-28,-1] window is incomplete for FED-23DEC.

## Data policy

Raw upstream daily CSVs are NOT committed to git.
The workflow downloads them from the public Diercks-Katz-Wright S3 bucket and stores raw
inputs only as temporary GitHub Actions artifacts.

Committed outputs are intentionally lightweight:
- `data/kalshi_fomc_factors.csv`
- `data/source_manifest.json`
- `data/fomc_contract_calendar.csv`

The manifest records SHA-256 hashes of all source files and the derived factor CSV.

## Research boundary

This branch is a data/replication layer. Paper-specific GARCH-MIDAS estimation, tables,
figures, manuscript text, and submission materials stay in DrFuliyang/research and the user's
Drive/Dropbox research archives.

## Citation

Please cite the upstream replication package and paper:
Diercks, Anthony M.; Katz, Jared Dean; Wright, Jonathan H. (2026).
*Kalshi and the Rise of Macro Markets*.

Any paper using this extension should separately describe and cite the GARCH-MIDAS
transformation developed by the extension author(s).
