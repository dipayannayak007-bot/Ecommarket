# Project Changelog

This file records meaningful, user-visible changes to the project. Dates refer to when the change was committed to the repository.

## 2026-11-13 — Analysis and reproducibility upgrade

- Corrected year-over-year growth calculations so observations separated by multiple years are not presented as consecutive annual growth.
- Refactored the Python analysis runner into reusable functions and a guarded entry point.
- Added input validation for the market dataset.
- Added scenario and sensitivity outputs, charts, and an HTML report generated from the analysis outputs.
- Added an exploratory K-Means consumer-segmentation workflow that requires consented survey responses, checks sample size, and reports silhouette scores.
- Added automated tests and a GitHub Actions workflow for compilation, tests, and report generation.
- Expanded setup instructions and documented the distinction between sourced market observations and illustrative modelling assumptions.

## Methodology notes

- Scenario growth rates and serviceable-market reachability values are modelling assumptions, not official forecasts.
- Consumer segments are exploratory. Results from a small or convenience sample should not be generalized to the entire Indian e-commerce market.
- No synthetic consumer or transaction records are treated as observed survey evidence.
