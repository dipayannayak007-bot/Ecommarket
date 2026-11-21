# 📊 CNT-02 — India E-Commerce Market Growth & Consumer Segmentation

> **A fully offline Python-based analysis** of India's e-commerce market with a focus on the Electronics & Appliances segment — now with validated clustering, forecast backtesting, and an interactive dashboard.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Status](https://img.shields.io/badge/Status-Complete-brightgreen)
![License](https://img.shields.io/badge/License-Academic-blue)
![Offline](https://img.shields.io/badge/Runtime-Fully%20Offline-orange)

---

## 📋 Project Description

This project is an academic research study analysing **India's rapidly growing e-commerce market**, with a focus on the **electronics and appliances** segment. It combines publicly available market data from **IBEF** and **NITI Aayog** with an original consumer survey instrument to study market growth trends, build illustrative scenario forecasts, and explore consumer segmentation.

The analysis is **fully offline** at runtime: the dashboard embeds its own JavaScript and all result data, so it opens in a browser with no server and no internet connection.

### 🎯 Objectives

- Visualise the trajectory of India's total e-commerce market (2021–2035) using official data
- Benchmark the electronics & appliances and smartphones sub-segments
- Build illustrative growth scenario projections (Conservative, Base, Optimistic)
- Estimate Total Addressable Market (TAM) and Serviceable Addressable Market (SAM)
- Design a consumer survey instrument for primary data collection
- **Fix and validate** the K-means segmentation pipeline using the survey's real ordinal columns
- **Evaluate** growth models with backtests, published-forecast benchmarks and prediction intervals
- **Deliver** a professional interactive dashboard for exploring every result
- Ensure the entire analysis runs **fully offline** — no APIs or internet dependencies

---

## 📁 Project Structure

```
CNT02_Python_Offline/
│
├── run_project.py              # Main analysis orchestrator — generates all charts and data
├── segmentation.py             # Ordinal encoding + validated K-means pipeline
├── forecast_validation.py      # Backtests, benchmarks, prediction intervals, sensitivity
├── dashboard.py                # Self-contained interactive HTML dashboard generator
├── generate_report.py          # PDF report generator
├── requirements.txt            # Python package dependencies
├── run_windows.bat             # Windows batch launcher
├── README.md                   # This file
├── .gitignore
│
├── scripts/
│   └── make_sample_survey.py   # Deterministic generator for the illustrative demo responses
│
├── data/
│   ├── india_ecommerce_market.csv   # Market data from IBEF and NITI Aayog (11 observations)
│   ├── survey_template.csv          # Schema for survey responses (14 fields)
│   ├── sample_survey_responses.csv  # 60 ILLUSTRATIVE SYNTHETIC responses for demonstration
│   ├── survey_responses.csv         # Real consented responses (local, git-ignored, optional)
│   └── README.md                    # Data documentation
│
├── docs/
│   └── survey_questionnaire.md      # Full 14-question consumer survey instrument
│
└── outputs/                         # Generated outputs (created on first run)
    ├── figures/                     # PNG chart files (01–15)
    ├── electronics_scenario_forecast.csv
    ├── exploratory_consumer_segments.csv
    ├── cluster_profiles.csv
    ├── k_selection.csv
    ├── segment_validation.csv
    ├── feature_significance.csv
    ├── forecast_backtest.csv
    ├── forecast_benchmark.csv
    ├── forecast_model_comparison.csv
    ├── growth_rate_benchmarks.csv
    ├── forecast_prediction_intervals.csv
    ├── cagr_sensitivity.csv
    ├── dashboard.html               # Interactive, fully offline results explorer
    └── CNT02_Project_Report.pdf
```

---

## 📊 Visualisations & Analysis

| # | Chart | Description |
|---|-------|-------------|
| 1 | **India E-Commerce Market Trend** | Reported values (2021–2024) vs IBEF forecasts (2025–2035) |
| 2 | **Electronics Category Benchmark** | Electronics & Appliances (US\$27bn) vs Smartphones (US\$39bn), 2024 |
| 3 | **Growth Scenario Projections** | 8% / 12% / 16% CAGR scenarios, 2024–2030 |
| 4 | **TAM vs SAM Sizing** | 2024 TAM vs illustrative SAM at 30% reachable share |
| 5–10 | Optional transaction / survey charts | When local data is supplied |
| 11 | **K Selection** | Silhouette and elbow/inertia for k = 2–6 |
| 12 | **Cluster Profiles** | Standardised influence-score heatmap by segment |
| 13 | **Cluster Scatter** | Respondents in a 2-D PCA projection |
| 14 | **Forecast Backtest** | Fitted models and rolling-origin prediction points |
| 15 | **IBEF Benchmark** | Model projections vs published forecasts with 95% prediction interval |

---

## 🔬 Statistical Validation

### K-means feature mismatch — fixed

The original pipeline searched for non-existent numeric columns (`emi_influence_score`, `exchange_influence_score`, `delivery_cost_influence_score`). The actual survey stores **ordinal text** answers in `emi_influence`, `exchange_influence` and `delivery_cost_influence`, so numeric coercion silently removed every row and no segmentation ran.

`segmentation.py` now:

1. Maps the questionnaire vocabulary explicitly: `Not at all` → 1, `A little` → 2, `Somewhat` → 3, `A lot` → 4 (price sensitivity and discount importance use 1–5).
2. Treats `Not applicable` / `Unsure` / `Not eligible` as **missing**, not as low influence.
3. Standardises the five features and evaluates **k = 2…6** using silhouette, inertia, Calinski–Harabasz and Davies–Bouldin.
4. Validates the chosen solution with 20 random seeds, 40 bootstrap resamples (Adjusted Rand Index) and a 100-permutation test.

### Results on the illustrative 60-response sample

| Check | Result |
|-------|--------|
| Valid responses used | 54 (6 rows had non-substantive "Unsure/N/A" answers) |
| Selected k (highest silhouette) | **3** (silhouette 0.295, vs 0.283 for k=2 and 0.284 for k=4) |
| Seed stability (mean ARI) | 0.948 |
| Bootstrap stability (mean ARI) | 0.710 (5th percentile 0.386) |
| Permutation test | observed silhouette 0.295 vs permuted mean 0.190, **p = 0.0099** |
| Per-feature Kruskal–Wallis tests | all five influence features differ across segments (p < 0.0001; η² = 0.38–0.65) |

| Segment | n | Profile |
|---------|---|---------|
| 1 — Cautious / low-influence | 15 (27.8%) | Low discount, EMI and price sensitivity; typical spend ₹1,000–4,999 |
| 2 — EMI-responsive + discount-driven | 17 (31.5%) | High EMI influence and discount importance; typical spend ₹15,000–29,999 |
| 3 — Exchange-motivated + delivery-cost-sensitive | 22 (40.7%) | High exchange and delivery-cost influence, high price sensitivity; spend ₹5,000–14,999 |

The bootstrap ARI of 0.71 indicates **moderate** — not perfect — stability, which is expected with a small sample. Segment names are interpretive labels, not market facts.

### Forecasting evaluation

`forecast_validation.py` fits four models (CAGR/log-linear, linear trend, Holt exponential smoothing, naive last value) to the **four reported** total-market observations and evaluates them two ways:

1. **Rolling-origin backtests** (train on earlier years, predict the next reported year; n = 2 per model).
2. **Published-forecast benchmark** — projections through 2035 compared with IBEF's published forecasts. These are *benchmarks, not observed outcomes*.

| Model | Backtest MAPE | IBEF benchmark MAPE |
|-------|--------------:|--------------------:|
| CAGR (log-linear) | **2.23%** | 42.34% |
| Linear trend | 2.76% | 18.14% |
| Holt exponential smoothing | 17.63% | **13.05%** |
| Naive (last value) | 18.02% | 44.54% |

**Interpretation:** the curved CAGR fit tracks the four recent points well but over-extrapolates over a 5–10 year horizon. This is precisely why the project presents a **scenario band** rather than one predicted number.

The fitted 2021–24 total-market CAGR is **22.94%** (analytic 95% CI 20.51%–25.41%, df = 2), above IBEF's implied 18.44% for 2024–2030 and well above the illustrative 8/12/16% electronics scenarios. Only four observations are available, so these are **diagnostics, not proof**.

---

## 🖥️ Interactive Dashboard

Run `python run_project.py`, then open **`outputs/dashboard.html`** in any modern browser. It is a single self-contained file (Plotly.js and all data embedded) — no server, no internet, no installation for the viewer.

| Tab | What you can explore |
|-----|----------------------|
| **Market overview** | Reported vs forecast trajectory, category benchmark, TAM/SAM |
| **Scenario explorer** | Live sliders for CAGR (4–28%), SAM share (5–60%) and 2024 TAM, with an updated chart and projection table |
| **Consumer segments** | PCA scatter of respondents, profile heatmap, segment cards and mean scores |
| **Statistical validation** | k-selection curves, stability/permutation metrics, backtests, model scorecard, growth benchmarks |
| **Data & methods** | Encoding map, provenance, assumptions and CSV download buttons |

---

## 🛒 Survey Design

A **14-question consumer survey** covering online electronics shopping behaviour in India:

| Section | Questions | Focus Area |
|---------|-----------|------------|
| 1. Consent | Q1 | Informed voluntary consent |
| 2. Demographics | Q2–Q4 | State/UT, residence type, age band |
| 3. Shopping Behaviour | Q5–Q7 | Online purchase history, category, frequency |
| 4. Spending & Sensitivity | Q8–Q10 | Spend band, price sensitivity, discount importance |
| 5. Purchase Influences | Q11–Q14 | EMI, exchange offers, delivery cost, price threshold |

Full survey: [`docs/survey_questionnaire.md`](docs/survey_questionnaire.md)

> **Data note:** `data/sample_survey_responses.csv` contains **60 synthetic demonstration responses** generated by `scripts/make_sample_survey.py` with three planted behavioural patterns. It exists so the clustering pipeline can be demonstrated reproducibly. It is **not real survey data**. For real analysis, place consented anonymised responses in `data/survey_responses.csv` (git-ignored); the pipeline prefers that file automatically.

---

## 🚀 How to Run

### Prerequisites
- Python 3.10 or higher
- pip (Python package manager)

### Setup & Execution

```bash
# 1. Clone the repository
git clone https://github.com/dipayannayak007-bot/ecom2.git
cd ecom2

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Run the full analysis (charts, validated models, CSVs and dashboard)
python run_project.py

# 4. Generate the PDF report
python generate_report.py
```

On Windows, you can also double-click `run_windows.bat`.

Useful options:

```bash
python run_project.py --no-open          # don't auto-open PNGs in Windows viewers
python run_project.py --tam 30 --sam-share 0.25
python run_project.py --survey data/survey_responses.csv
python run_project.py --no-dashboard     # skip the HTML build
```

> **Note:** After installing dependencies, the entire analysis runs **fully offline** — no internet connection needed.

---

## 🛠 Technology Stack

| Component | Technology |
|-----------|------------|
| Language | Python 3.10+ |
| Data Processing | NumPy (≥1.24), pandas (≥2.0) |
| Visualisation | Matplotlib (≥3.7), Plotly (≥5.18, embedded in the dashboard) |
| Clustering & statistics | scikit-learn (≥1.3), SciPy (≥1.10) — silhouette, ARI, t-intervals |
| PDF Generation | fpdf2 |
| Runtime | Fully offline — no APIs or network calls |

---

## 📊 Key Findings

- India's total e-commerce market grew from **US\$67bn** (2021) to **US\$125bn** (2024) — an **86% increase** over 3 years
- IBEF forecasts project growth to **US\$345bn** by 2030 and **US\$550bn** by 2035
- The online electronics & appliances segment was estimated at **US\$27bn** in 2024
- Under the base case (12% CAGR), electronics TAM roughly doubles to **US\$53.3bn** by 2030
- Three consumer segments were recovered from the demo survey and passed a permutation test (p = 0.0099)
- Short-horizon backtests favour the CAGR model, but long-horizon benchmarks favour flatter growth — scenario ranges are essential

---

## 📚 Data Sources & References

| # | Source | Description |
|---|--------|-------------|
| 1 | [IBEF (2025)](https://www.ibef.org/uploads/industry/Infrographics/large/e-Commerce-%20infographics-august-2025.pdf) | India E-Commerce Infographic, August 2025 |
| 2 | [NITI Aayog (2026)](https://niti.gov.in/sites/default/files/2026-02/Trade-Watch-Quarterly-July-September-Q2-FY-2025-26.pdf) | Trade Watch Quarterly, Q2 FY 2025-26 |
| 3 | [MoSPI HCES](https://microdata.gov.in/NADA/index.php/catalog/CEXP) | Household Consumer Expenditure Survey |

---

## ⚠️ Assumptions & Limitations

### Assumptions
- Scenario CAGRs (8%, 12%, 16%) are **illustrative**, not official forecasts
- Default SAM reachability factor of 30% is an assumption for sizing exercises
- IBEF's 2025+ values are forecasts published in that source, not measured outcomes

### Limitations
- The bundled 60 survey responses are **synthetic demonstration data**, not a real sample
- Convenience survey samples are not nationally representative
- Self-reported price sensitivity ≠ observed price elasticity
- K-means segmentation is exploratory: bootstrap ARI ≈ 0.71 shows only moderate stability at n = 54
- Only **four** reported market observations exist; the backtest has n = 2 per model and the fitted CAGR interval is wide (df = 2)
- IBEF forecast points are projections, so the "benchmark" comparison measures consistency with another forecast, not predictive accuracy
- MoSPI HCES measures household consumption expenditure, not online transactions

---

## 🔮 Future Work

- Collect primary survey data across diverse Indian states and demographic groups
- Validate scenario assumptions against additional industry reports
- Incorporate transaction data analysis for empirical purchasing pattern insights
- Re-run the stability suite once a larger real sample is available
- Add regional (state-level) analysis of e-commerce adoption
- Fit ARIMA / state-space models when a longer observed time series becomes available

---

## 👤 Author

**Dipayan Nayak**

---

*This project is for academic and research purposes only.*
