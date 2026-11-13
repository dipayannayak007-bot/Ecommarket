# CNT-02 — India E-Commerce Market Growth and Consumer Segmentation

A reproducible research and analytics project examining India's e-commerce market,
with an initial focus on online electronics and appliances.

## Project components

- `Project_Notebook.Rmd`: research notebook, source notes, market sizing,
  scenario analysis and data-gated survey/transaction templates.
- `analysis/`: R scripts for scenario modelling and conditional visuals.
- `data/`: published market benchmarks and blank survey schema.
- `docs/survey_questionnaire.md`: voluntary, anonymised consumer questionnaire.
- `python/`: reproducible Python market analysis, HTML report, charts, tables
  and an optional real-data consumer clustering workflow.

## Run the Python analysis

Install dependencies once:

```bash
python -m pip install -r python/requirements.txt
```

Generate the market report:

```bash
python python/run_project.py
```

Outputs: six PNG charts, three CSV tables and
`python/reports/Project_Report.html`.

## Consumer segmentation

Segmentation requires actual, consented survey responses. No respondent data is
included or fabricated. Follow the questionnaire and data schema, save the
anonymised response file locally as `python/data/survey_responses.csv`, and run:

```bash
python python/segment_consumers.py --input python/data/survey_responses.csv
```

The script checks consent and minimum sample adequacy before exploratory K-Means
clustering. A convenience sample must not be described as nationally representative.

## Evidence and assumptions

- The 2024 India online electronics-and-appliances market benchmark is US$27bn,
  attributed in the notebook to NITI Aayog Trade Watch Q2 FY2025-26.
- The total e-commerce series is attributed to IBEF's August 2025 infographic.
- Scenario growth rates (8%, 12%, 16%) and the 30% SAM reachability share are
  illustrative assumptions, not official forecasts or measured market shares.
- HCES household expenditure is contextual data, not a direct record of online orders.
- Category benchmarks are not added together where their definitions may overlap.

## Reproducibility and privacy

Python outputs are generated from committed source data. R outputs are generated
locally. Private survey responses, transaction extracts and restricted microdata
must not be committed. See `data/README.md` and the notebook for data-use notes.

## Project status

Published benchmark analysis and survey design are implemented. Primary survey
collection, permitted transaction-data acquisition and empirical validation remain
future research steps.
