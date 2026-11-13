# CNT-02 — Python analysis

## Quick start

From the repository root:

```bash
python -m pip install -r python/requirements.txt
python python/run_project.py
```

Or from this directory:

```bash
python -m pip install -r requirements.txt
python run_project.py
```

The analysis reads the committed market benchmark CSV and creates six PNG charts,
three CSV tables and `reports/Project_Report.html`. Outputs are reproducible and
written under `python/reports/`.

## Consumer segmentation (data required)

The clustering workflow is deliberately separate and does not fabricate survey
responses. Collect voluntary, anonymised responses using
`../docs/survey_questionnaire.md`, retain consent, and place the completed CSV at
`data/survey_responses.csv` (this file is git-ignored).

Then run:

```bash
python segment_consumers.py --input data/survey_responses.csv
```

The script excludes non-consenting rows, checks sample adequacy, tests K-Means
solutions for k=2..6 (bounded by sample size), selects the highest silhouette
score and saves assignments, cluster profiles and scores to
`reports/segmentation/`. This is exploratory analysis, not proof of naturally
occurring or nationally representative segments. Review cluster profiles before
assigning business labels.

## Methodological safeguards

- Reported market values and published forecasts remain distinct.
- Annual growth is calculated only where consecutive calendar years exist;
  a four-year gap is never mislabeled as year-on-year growth.
- TAM/SAM scenarios are assumptions, not official forecasts.
- No transaction histogram is produced without actual transaction records.
- Do not commit identifiable survey responses, restricted microdata or credentials.
