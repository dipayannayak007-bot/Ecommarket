# CNT-02 — India E-Commerce Market Growth and Consumer Segmentation

R Markdown research notebook for India's e-commerce market, initially focusing on electronics and appliances.

## Repository contents

- `Project_Notebook.Rmd` — main R Markdown notebook with data sourcing, market context, TAM/SAM model, scenario forecast and analysis templates.
- `analysis/market_scenarios.R` — standalone reproducible TAM/SAM and scenario calculation.
- `data/india_ecommerce_market.csv` — published market benchmark series, with forecasts labelled.
- `data/survey_template.csv` — blank primary consumer survey response schema.
- `data/README.md` — data provenance, transaction schema and privacy notes.
- `docs/survey_questionnaire.md` — draft questionnaire.
- `.gitignore` — excludes local/private data and rendered outputs.

## Run the scenario script

From the repository root:

~~~sh
Rscript analysis/market_scenarios.R
~~~

The script writes `outputs/electronics_scenario_forecast.csv` locally.

## Run the notebook

Install R and RStudio, then run:

~~~r
install.packages(c("rmarkdown", "knitr", "tidyverse", "scales",
                   "lubridate", "janitor"))
rmarkdown::render("Project_Notebook.Rmd")
~~~

## Evidence and assumptions

- Published 2024 category benchmark: US$27bn for India's online electronics and appliances market, cited to NITI Aayog Trade Watch Q2 FY2025-26.
- Scenario CAGRs (8%, 12%, 16%) and 30% SAM reachability factor are illustrative modelling assumptions, not observed market shares or official forecasts.
- MoSPI HCES is household consumption expenditure data, not an online transaction database.
- No fabricated survey or transaction records are included. Empirical segmentation requires actual consented responses.

## Privacy

Do not commit identifiable respondent information, restricted microdata, credentials or personal data. See `data/README.md`.

## Status

Initial research design, published benchmarks, survey instrument and scenario model are in place. Survey collection, data acquisition and empirical validation remain pending.
