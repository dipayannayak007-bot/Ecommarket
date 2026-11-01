# CNT-02 — India E-Commerce Market Growth and Consumer Segmentation

R Markdown research notebook for India's e-commerce market, initially focusing on electronics and appliances.

## Objectives
- Describe Indian e-commerce market trends and consumer behaviour.
- Segment consumers by category preference, price sensitivity and purchase frequency.
- Estimate category TAM and an assumption-based SAM.
- Compare conservative, base and optimistic market-growth scenarios.

## Structure
- Project_Notebook.Rmd — main reproducible analysis notebook
- data/survey_template.csv — blank schema for primary consumer survey responses
- data/README.md — data provenance, transaction schema and privacy notes
- docs/survey_questionnaire.md — draft questionnaire

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
Do not commit identifiable respondent information, restricted microdata, credentials or personal data. See data/README.md.

## Status
Initial research design, published benchmarks, survey instrument and scenario model are in place. Survey collection, data acquisition and empirical validation remain pending.
