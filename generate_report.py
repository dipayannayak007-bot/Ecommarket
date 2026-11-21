#!/usr/bin/env python3
"""Generate a PDF project report for CNT-02.

Run:  python generate_report.py

Produces  outputs/CNT02_Project_Report.pdf
No internet connection is needed at runtime.
"""
from pathlib import Path
from datetime import date
import csv
import math
import os
import sys
import subprocess

try:
    from fpdf import FPDF
except ImportError:
    print("fpdf2 not found. Installing now...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "fpdf2"])
    from fpdf import FPDF

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FIG = OUT / "figures"
REPORT_PATH = OUT / "CNT02_Project_Report.pdf"


# ---- data helpers (stdlib only; tolerant of missing / partial outputs) ----

def read_rows(path: Path) -> list[dict]:
    """Read a CSV as a list of dict rows; return [] if it is absent or unreadable."""
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8-sig") as handle:
            return list(csv.DictReader(handle))
    except (OSError, csv.Error):
        return []


def fmt(value, default="n/a") -> str:
    """Safe ASCII display string for a possibly missing CSV cell."""
    if value is None:
        return default
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none", "null", "<na>"}:
        return default
    return text


def num(value, decimals: int = 2, default: str = "n/a") -> str:
    """Format a numeric CSV cell defensively (NaN / blanks become the default)."""
    if value is None:
        return default
    try:
        number = float(str(value).strip())
    except (TypeError, ValueError):
        return default
    if not math.isfinite(number):
        return default
    return f"{number:.{decimals}f}"


def not_generated(pdf, name: str) -> None:
    """Show a short note when an expected generated output is not available."""
    pdf.body_text(f"[{name}: not yet generated. Run the analysis pipeline first.]")


class ReportPDF(FPDF):
    """Custom FPDF subclass with header / footer branding."""

    def header(self):
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(100, 100, 100)
        self.cell(0, 8, "CNT-02  |  India E-Commerce Market Growth & Consumer Segmentation", align="L")
        self.ln(4)
        self.set_draw_color(60, 130, 100)
        self.set_line_width(0.4)
        self.line(10, self.get_y(), self.w - 10, self.get_y())
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(140, 140, 140)
        self.cell(0, 10, f"Page {self.page_no()}/{{nb}}", align="C")

    # ---- helper methods ----

    def chapter_title(self, number, title):
        """Add a numbered chapter heading."""
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(30, 80, 60)
        self.cell(0, 12, f"{number}. {title}", new_x="LMARGIN", new_y="NEXT")
        self.set_draw_color(60, 130, 100)
        self.set_line_width(0.3)
        self.line(10, self.get_y(), 90, self.get_y())
        self.ln(6)

    def section_title(self, title):
        """Add a sub-section heading."""
        self.set_font("Helvetica", "B", 12)
        self.set_text_color(50, 50, 50)
        self.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        """Add body paragraph text."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def bullet(self, text):
        """Add a bullet-point line."""
        self.set_font("Helvetica", "", 10)
        self.set_text_color(40, 40, 40)
        x = self.get_x()
        self.cell(6, 5.5, "-")
        self.multi_cell(0, 5.5, text)
        self.ln(1)

    def add_figure(self, path, caption, width=170):
        """Embed a PNG figure with a caption.  Skips if the file is missing."""
        if not path.exists():
            self.body_text(f"[Figure not found: {path.name}]")
            return
        # Check remaining space; add page if tight
        if self.get_y() > self.h - 100:
            self.add_page()
        self.image(str(path), x=20, w=width)
        self.ln(2)
        self.set_font("Helvetica", "I", 9)
        self.set_text_color(80, 80, 80)
        self.cell(0, 5, caption, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(6)

    def add_table(self, headers, rows, col_widths=None):
        """Draw a simple table."""
        if col_widths is None:
            col_widths = [self.epw / len(headers)] * len(headers)
        # Header row
        self.set_font("Helvetica", "B", 9)
        self.set_fill_color(60, 130, 100)
        self.set_text_color(255, 255, 255)
        for w, h in zip(col_widths, headers):
            self.cell(w, 7, h, border=1, align="C", fill=True)
        self.ln()
        # Data rows
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        fill = False
        for row in rows:
            if fill:
                self.set_fill_color(235, 245, 240)
            for w, val in zip(col_widths, row):
                self.cell(w, 6.5, str(val), border=1, align="C", fill=fill)
            self.ln()
            fill = not fill
        self.ln(4)

    def ensure_space(self, needed: float) -> None:
        """Start a new page if there is not enough room for a table block."""
        if self.get_y() + needed > self.h - 20:
            self.add_page()


def build_report():
    pdf = ReportPDF(orientation="P", unit="mm", format="A4")
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =====================================================================
    #  TITLE PAGE
    # =====================================================================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_text_color(30, 80, 60)
    pdf.cell(0, 14, "Project Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_font("Helvetica", "", 18)
    pdf.set_text_color(60, 60, 60)
    pdf.cell(0, 10, "CNT-02: India E-Commerce Market Growth", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 10, "and Consumer Segmentation", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(8)

    pdf.set_draw_color(60, 130, 100)
    pdf.set_line_width(0.6)
    pdf.line(60, pdf.get_y(), pdf.w - 60, pdf.get_y())
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 8, "A Fully Offline Python Analysis", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 8, "Electronics & Appliances Segment Focus", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(16)

    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 7, f"Date: {date.today().strftime('%B %d, %Y')}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Language: Python 3.10+", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 7, "Runtime: Fully offline (no APIs / no network calls)", align="C", new_x="LMARGIN", new_y="NEXT")

    # =====================================================================
    #  TABLE OF CONTENTS
    # =====================================================================
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(30, 80, 60)
    pdf.cell(0, 12, "Table of Contents", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(6)

    toc_items = [
        ("1", "Executive Summary"),
        ("2", "Introduction & Objectives"),
        ("3", "Data Sources & Evidence"),
        ("4", "Methodology"),
        ("5", "Market Analysis & Visualisations"),
        ("6", "Scenario Forecasting"),
        ("7", "Survey Design"),
        ("8", "Consumer Segmentation Approach"),
        ("9", "Project Architecture"),
        ("10", "Results Summary"),
        ("11", "Limitations & Future Work"),
        ("12", "References"),
        ("13", "Statistical Validation & Interactive Dashboard"),
    ]
    pdf.set_font("Helvetica", "", 12)
    pdf.set_text_color(50, 50, 50)
    for toc_num, title in toc_items:
        pdf.cell(10, 8, toc_num + ".")
        pdf.cell(0, 8, title, new_x="LMARGIN", new_y="NEXT")

    # =====================================================================
    #  1. EXECUTIVE SUMMARY
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("1", "Executive Summary")
    pdf.body_text(
        "This report documents the CNT-02 project, an offline Python-based analysis of India's "
        "e-commerce market with an initial focus on the electronics and appliances segment. "
        "The project combines publicly available market data from IBEF and NITI Aayog with "
        "an original consumer survey instrument to study market growth trends, build illustrative "
        "scenario forecasts, and explore consumer segmentation."
    )
    pdf.body_text(
        "Key findings from the market data analysis show that India's total e-commerce market "
        "reached US$125 billion in 2024 (IBEF), with the online electronics and appliances "
        "sub-segment estimated at US$27 billion and online smartphones at US$39 billion "
        "(NITI Aayog). The project generates three growth scenarios (Conservative at 8% CAGR, "
        "Base at 12% CAGR, and Optimistic at 16% CAGR) projecting the electronics TAM from "
        "2024 to 2030, alongside an illustrative SAM at 30% reachable share."
    )
    pdf.body_text(
        "A 14-question consumer survey covers demographics, online shopping behaviour, spending "
        "patterns, price sensitivity, and purchase influences (EMI, exchange offers, delivery "
        "cost). The validated segmentation pipeline reads the five ordinal TEXT survey columns, "
        "maps the questionnaire vocabulary to 1-5 scores, standardises them and automatically "
        "selects k from 2 to 6 by silhouette score. Seed stability, 80% bootstrap ARI and a "
        "100-shuffle permutation test check whether the solution is trustworthy."
    )
    pdf.body_text(
        "The bundled 60 responses in data/sample_survey_responses.csv are ILLUSTRATIVE SYNTHETIC "
        "data generated by scripts/make_sample_survey.py; real consented responses belong in "
        "data/survey_responses.csv. Statistical validation adds rolling-origin backtests, "
        "benchmarks against published IBEF forecasts and prediction intervals, all with honest "
        "small-sample caveats: only four reported market observations (2021-2024) exist, leaving "
        "two backtest points per model. A self-contained offline HTML dashboard "
        "(outputs/dashboard.html) presents the results interactively with no server or internet."
    )

    # =====================================================================
    #  2. INTRODUCTION & OBJECTIVES
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("2", "Introduction & Objectives")
    pdf.body_text(
        "India's e-commerce market has experienced rapid growth, driven by rising internet "
        "penetration, affordable smartphones, digital payment infrastructure (UPI), and a large "
        "young population. The electronics and appliances category is one of the highest-value "
        "segments in online retail, making it a compelling area for academic study."
    )
    pdf.section_title("Project Objectives")
    pdf.bullet("Visualise the trajectory of India's total e-commerce market (2021-2035) using official data.")
    pdf.bullet("Benchmark the electronics & appliances and smartphones sub-segments.")
    pdf.bullet("Build illustrative growth scenario projections (Conservative, Base, Optimistic).")
    pdf.bullet("Estimate a Total Addressable Market (TAM) and Serviceable Addressable Market (SAM).")
    pdf.bullet("Design a consumer survey instrument for primary data collection.")
    pdf.bullet("Provide an exploratory K-means clustering pipeline for consumer segmentation.")
    pdf.bullet("Ensure the entire analysis runs fully offline with no API or internet dependencies.")

    # =====================================================================
    #  3. DATA SOURCES & EVIDENCE
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("3", "Data Sources & Evidence")

    pdf.section_title("3.1 India E-Commerce Market Data")
    pdf.body_text(
        "The primary market dataset (data/india_ecommerce_market.csv) contains 11 observations "
        "drawn from two authoritative sources:"
    )

    headers = ["Year", "Value (US$ bn)", "Status", "Scope", "Source"]
    rows = [
        ["2021", "67", "Reported", "Total e-commerce", "IBEF"],
        ["2022", "84", "Reported", "Total e-commerce", "IBEF"],
        ["2023", "102", "Reported", "Total e-commerce", "IBEF"],
        ["2024", "125", "Reported", "Total e-commerce", "IBEF"],
        ["2025", "145", "Forecast", "Total e-commerce", "IBEF"],
        ["2026", "163", "Forecast", "Total e-commerce", "IBEF"],
        ["2030", "345", "Forecast", "Total e-commerce", "IBEF"],
        ["2035", "550", "Forecast", "Total e-commerce", "IBEF"],
        ["2024", "27", "Estimate", "Online electronics", "NITI Aayog"],
        ["2024", "39", "Estimate", "Online smartphones", "NITI Aayog"],
    ]
    col_w = [18, 28, 24, 48, 44]
    # Check space
    if pdf.get_y() > pdf.h - 100:
        pdf.add_page()
    pdf.add_table(headers, rows, col_w)

    pdf.section_title("3.2 Key Assumptions")
    pdf.bullet("Scenario CAGRs (8%, 12%, 16%) are illustrative, not official forecasts.")
    pdf.bullet("Default SAM reachability factor of 30% is an assumption for sizing exercises.")
    pdf.bullet("IBEF's 2025+ values are forecasts published in that source, not measured outcomes.")
    pdf.bullet("NITI Aayog's electronics and smartphones are separate, non-overlapping categories.")

    # =====================================================================
    #  4. METHODOLOGY
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("4", "Methodology")

    pdf.section_title("4.1 Market Trend Analysis")
    pdf.body_text(
        "Historical and forecast market values are plotted as a time-series line chart, "
        "distinguishing reported values from forecast projections using different series. "
        "This allows visual assessment of the growth trajectory and the gap between actuals "
        "and forecasts."
    )

    pdf.section_title("4.2 Category Benchmarking")
    pdf.body_text(
        "A horizontal bar chart compares the 2024 market sizes of the two electronics "
        "sub-categories (Electronics & Appliances at US$27bn versus Smartphones at US$39bn) "
        "to contextualise the target segment within the broader electronics vertical."
    )

    pdf.section_title("4.3 Scenario Forecasting")
    pdf.body_text(
        "Three compound annual growth rate (CAGR) scenarios are applied to the 2024 electronics "
        "TAM (US$27bn) and projected forward to 2030:"
    )
    pdf.bullet("Conservative: 8% CAGR - yields US$42.8bn by 2030")
    pdf.bullet("Base: 12% CAGR - yields US$53.3bn by 2030")
    pdf.bullet("Optimistic: 16% CAGR - yields US$65.8bn by 2030")
    pdf.body_text(
        "The formula used is:  TAM(year) = TAM(2024) x (1 + CAGR) ^ (year - 2024). "
        "An illustrative SAM is computed as 30% of the projected TAM."
    )

    pdf.section_title("4.4 Consumer Segmentation (Validated)")
    pdf.body_text(
        "The five ordinal survey columns - price_sensitivity, discount_importance, "
        "emi_influence, exchange_influence and delivery_cost_influence - are converted from "
        "their exact questionnaire wording to 1-5 scores (for example, 'Not at all'=1, "
        "'A little'=2, 'Somewhat'=3, 'A lot'=4; 'Not applicable'/'Unsure' count as missing). "
        "No pre-coded numeric *_influence_score columns are required. Rows with missing "
        "answers are dropped, the remaining features are StandardScaler-normalised, and a "
        "minimum of 10 valid responses is required."
    )
    pdf.body_text(
        "K-means is fitted for k=2..6 and compared on silhouette, inertia, Calinski-Harabasz "
        "and Davies-Bouldin scores; k is chosen automatically by the highest silhouette rather "
        "than fixed in advance. The chosen solution is then checked with label agreement across "
        "random seeds, adjusted Rand index on 80% bootstrap resamples, and a 100-shuffle "
        "permutation test of the observed silhouette."
    )

    # =====================================================================
    #  5. MARKET ANALYSIS & VISUALISATIONS
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("5", "Market Analysis & Visualisations")

    pdf.section_title("5.1 India E-Commerce Market Trend")
    pdf.body_text(
        "The chart below shows India's total e-commerce market from 2021 to 2035, "
        "distinguishing reported values (2021-2024) from IBEF forecasts (2025 onwards). "
        "The market grew from US$67bn in 2021 to US$125bn in 2024 and is forecast to "
        "reach US$550bn by 2035."
    )
    pdf.add_figure(FIG / "01_india_market_trend.png",
                   "Figure 1: India e-commerce market - reported values and forecasts (Source: IBEF)")

    pdf.section_title("5.2 Electronics Category Benchmark")
    pdf.body_text(
        "The horizontal bar chart compares the two online electronics categories reported "
        "by NITI Aayog for 2024. Smartphones (US$39bn) is a larger category than Electronics "
        "& Appliances (US$27bn), though they are classified as separate segments."
    )
    pdf.add_figure(FIG / "02_category_benchmark.png",
                   "Figure 2: Selected online electronics categories in India, 2024 (Source: NITI Aayog)")

    # =====================================================================
    #  6. SCENARIO FORECASTING
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("6", "Scenario Forecasting")

    pdf.section_title("6.1 Growth Scenario Projections")
    pdf.body_text(
        "The three growth scenarios project the electronics & appliances TAM from 2024 to 2030. "
        "Under the base case (12% CAGR), the market roughly doubles to US$53.3bn by 2030. "
        "The conservative and optimistic scenarios bracket this at US$42.8bn and US$65.8bn "
        "respectively."
    )
    pdf.add_figure(FIG / "03_tam_scenarios.png",
                   "Figure 3: Electronics & appliances - illustrative growth scenarios (2024-2030)")

    pdf.section_title("6.2 Scenario Forecast Data")
    # Condensed table - 2024 and 2030 endpoints only
    headers2 = ["Scenario", "CAGR", "TAM 2024", "TAM 2030", "SAM 2030"]
    rows2 = [
        ["Conservative", "8%", "$27.0bn", "$42.8bn", "$12.9bn"],
        ["Base", "12%", "$27.0bn", "$53.3bn", "$16.0bn"],
        ["Optimistic", "16%", "$27.0bn", "$65.8bn", "$19.7bn"],
    ]
    pdf.add_table(headers2, rows2, [34, 20, 34, 34, 34])

    pdf.section_title("6.3 TAM vs SAM Sizing")
    pdf.body_text(
        "The chart below compares the 2024 Total Addressable Market (US$27bn) to the "
        "illustrative Serviceable Addressable Market (US$8.1bn), computed at a 30% reachable "
        "share. This SAM factor is an assumption and must be validated with actual market "
        "evidence and competitive analysis."
    )
    pdf.add_figure(FIG / "04_tam_sam.png",
                   "Figure 4: 2024 India electronics & appliances - TAM vs illustrative SAM")

    # =====================================================================
    #  7. SURVEY DESIGN
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("7", "Survey Design")

    pdf.body_text(
        "A 14-question consumer survey instrument has been designed to collect primary data "
        "on online electronics shopping behaviour in India. The survey is structured in five "
        "sections with built-in consent and privacy protections."
    )

    pdf.section_title("7.1 Survey Structure")
    headers3 = ["Section", "Questions", "Focus Area"]
    rows3 = [
        ["1. Consent", "Q1", "Informed voluntary consent"],
        ["2. Demographics", "Q2-Q4", "State/UT, residence type, age band"],
        ["3. Shopping Behaviour", "Q5-Q7", "Online purchase history, category, frequency"],
        ["4. Spending & Sensitivity", "Q8-Q10", "Spend band, price sensitivity, discount importance"],
        ["5. Purchase Influences", "Q11-Q14", "EMI, exchange, delivery cost, price threshold"],
    ]
    pdf.add_table(headers3, rows3, [40, 24, 102])

    pdf.section_title("7.2 Key Design Principles")
    pdf.bullet("Anonymous: no name, phone number, exact address, or payment details collected.")
    pdf.bullet("Voluntary: respondents may skip any question or stop at any time.")
    pdf.bullet("Brief: estimated completion time of 3-5 minutes to maximise response rates.")
    pdf.bullet("Categorical responses: ordinal scales and bands used for quantitative analysis.")

    pdf.section_title("7.3 Data Schema")
    pdf.body_text(
        "Survey responses are stored in data/survey_responses.csv following the schema defined "
        "in data/survey_template.csv with 14 fields: respondent_id, state_ut, residence_type, "
        "age_band, online_purchase_12m, preferred_category, purchase_frequency_12m, "
        "spend_band_inr, price_sensitivity, discount_importance, emi_influence, "
        "exchange_influence, delivery_cost_influence, and consent."
    )

    # =====================================================================
    #  8. CONSUMER SEGMENTATION APPROACH
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("8", "Consumer Segmentation Approach")

    pdf.body_text(
        "The project includes a validated K-means pipeline for exploratory consumer "
        "segmentation. It works directly with the real survey schema: the ordinal TEXT answers "
        "to five influence questions, not pre-coded numeric influence scores."
    )

    pdf.section_title("8.1 Clustering Pipeline")
    pdf.bullet("Features: price_sensitivity, discount_importance, emi_influence, exchange_influence, delivery_cost_influence")
    pdf.bullet("Encoding: exact questionnaire vocabulary mapped to 1-5 ('Not at all'/'Slightly'/'Moderately'/'Very'/'Extremely' for price sensitivity; 'Not at all'/'A little'/'Somewhat'/'A lot' for the three influence questions; 1-5 for discount importance)")
    pdf.bullet("Missing answers: 'Not applicable', 'Unsure' and blanks are excluded, not scored as low influence")
    pdf.bullet("Pre-processing: StandardScaler normalisation to zero mean, unit variance; at least 10 complete responses")
    pdf.bullet("k selection: K-means fitted for k=2..6 and compared by silhouette, inertia, Calinski-Harabasz and Davies-Bouldin; best silhouette chosen automatically")
    pdf.bullet("Validation: seed stability, 80% bootstrap adjusted Rand index, and a 100-shuffle permutation test of the silhouette")
    pdf.bullet("Outputs: exploratory_consumer_segments.csv, cluster_profiles.csv, k_selection.csv, segment_validation.csv and figures 11-13")

    pdf.section_title("8.2 Interpretation Guidance")
    pdf.body_text(
        "Clusters are profiled by their mean influence scores and given descriptive labels, but "
        "they remain exploratory. The bundled 60 responses are illustrative synthetic data used "
        "to demonstrate the workflow, so the segments are not evidence about real consumers. "
        "Conclusions require real consented responses in data/survey_responses.csv and a larger, "
        "representative sample; the automated validation checks describe stability, not "
        "market truth."
    )

    # =====================================================================
    #  9. PROJECT ARCHITECTURE
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("9", "Project Architecture")

    pdf.section_title("9.1 Technology Stack")
    pdf.bullet("Language: Python 3.10+")
    pdf.bullet("Core libraries: NumPy (>=1.24), pandas (>=2.0), Matplotlib (>=3.7)")
    pdf.bullet("scikit-learn (>=1.3) for validated K-means clustering; SciPy for statistical tests")
    pdf.bullet("Optional: Plotly for the self-contained offline HTML dashboard")
    pdf.bullet("Report generation: fpdf2")
    pdf.bullet("Runtime: Fully offline - no API calls or internet access at runtime")

    pdf.section_title("9.2 Project Structure")
    structure = [
        ["run_project.py", "Main analysis script - generates all charts and data"],
        ["generate_report.py", "PDF report generator (this script)"],
        ["segmentation.py", "Ordinal encoding, k selection and segment validation"],
        ["forecast_validation.py", "Backtests, benchmarks, intervals, CAGR diagnostics"],
        ["dashboard.py", "Builds the self-contained offline HTML dashboard"],
        ["requirements.txt", "Python package dependencies"],
        ["run_windows.bat", "Windows batch launcher"],
        ["data/", "Input data directory"],
        ["  india_ecommerce_market.csv", "Market data from IBEF and NITI Aayog"],
        ["  survey_template.csv", "Schema for survey responses"],
        ["  sample_survey_responses.csv", "60 illustrative synthetic demo responses"],
        ["scripts/", "Data generation helpers"],
        ["  make_sample_survey.py", "Reproducible synthetic sample generator"],
        ["docs/", "Documentation"],
        ["  survey_questionnaire.md", "Full survey instrument (14 questions)"],
        ["outputs/", "Generated outputs"],
        ["  figures/", "PNG charts 01-15 (11-13 segments, 14-15 validation)"],
        ["  electronics_scenario_forecast.csv", "Scenario projection data"],
        ["  exploratory_consumer_segments.csv", "Respondent-level cluster assignments"],
        ["  cluster_profiles.csv", "Segment profiles and influence means"],
        ["  k_selection.csv", "k=2..6 diagnostic metrics"],
        ["  segment_validation.csv", "Stability, bootstrap and permutation results"],
        ["  feature_significance.csv", "Kruskal-Wallis p-values and effect sizes"],
        ["  forecast_model_comparison.csv", "Backtest / benchmark scorecard"],
        ["  growth_rate_benchmarks.csv", "CAGR estimates, CIs and assumptions"],
        ["  dashboard.html", "Interactive offline dashboard (embedded Plotly.js)"],
        ["  CNT02_Project_Report.pdf", "This project report"],
    ]
    headers4 = ["File / Directory", "Description"]
    pdf.add_table(headers4, structure, [70, 96])

    pdf.add_page()
    pdf.section_title("9.3 Execution Flow")
    pdf.body_text(
        "1. setup() creates the output directories.\n"
        "2. market_data() loads the CSV dataset.\n"
        "3. save_market_trend() generates the time-series line chart (Figure 1).\n"
        "4. save_category_chart() generates the category benchmark bar chart (Figure 2).\n"
        "5. scenario_table() computes and exports the 3-scenario forecast CSV.\n"
        "6. save_scenario_chart() generates the scenario projection chart (Figure 3).\n"
        "7. save_tam_sam() generates the TAM vs SAM chart (Figure 4).\n"
        "8. analyse_transactions() processes optional transaction data (Figures 5-6).\n"
        "9. analyse_survey() processes optional survey data (Figures 7-10); it no longer attempts K-means.\n"
        "10. segmentation.run() encodes the five ordinal columns, selects k=2..6 by silhouette, runs stability, permutation and per-feature tests.\n"
        "11. forecast_validation.run() runs backtests, IBEF benchmarks, prediction intervals and CAGR diagnostics.\n"
        "12. dashboard.build() embeds every result and Plotly.js into outputs/dashboard.html for offline viewing."
    )

    # =====================================================================
    #  10. RESULTS SUMMARY
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("10", "Results Summary")

    pdf.section_title("10.1 Market Growth")
    pdf.bullet("India's total e-commerce market grew from US$67bn (2021) to US$125bn (2024) - an 86% increase over 3 years.")
    pdf.bullet("IBEF forecasts project growth to US$345bn by 2030 and US$550bn by 2035.")
    pdf.bullet("The online electronics & appliances segment was estimated at US$27bn in 2024.")

    pdf.section_title("10.2 Scenario Projections")
    pdf.bullet("Conservative (8% CAGR): Electronics TAM reaches US$42.8bn by 2030.")
    pdf.bullet("Base (12% CAGR): Electronics TAM reaches US$53.3bn by 2030.")
    pdf.bullet("Optimistic (16% CAGR): Electronics TAM reaches US$65.8bn by 2030.")
    pdf.bullet("At 30% SAM share, the base-case addressable market is US$16.0bn by 2030.")

    pdf.section_title("10.3 Outputs Generated")
    pdf.bullet("4 core visualisation charts (Figures 1-4)")
    pdf.bullet("Scenario forecast CSV with 21 data points (3 scenarios x 7 years)")
    pdf.bullet("Survey instrument with 14 questions across 5 sections")
    pdf.bullet("Optional: transaction analysis charts (Figures 5-10)")
    pdf.bullet("Segmentation: exploratory_consumer_segments.csv, cluster_profiles.csv, k_selection.csv, segment_validation.csv, feature_significance.csv and Figures 11-13")
    pdf.bullet("Validation: forecast_backtest.csv, forecast_benchmark.csv, forecast_model_comparison.csv, growth_rate_benchmarks.csv, forecast_prediction_intervals.csv, cagr_sensitivity.csv and Figures 14-15")
    pdf.bullet("outputs/dashboard.html: interactive, fully offline dashboard (no server or internet)")
    pdf.body_text(
        "Survey-based results currently use the 60 illustrative synthetic responses in "
        "data/sample_survey_responses.csv; replace them with real consented responses before "
        "drawing substantive conclusions."
    )

    # =====================================================================
    #  11. LIMITATIONS & FUTURE WORK
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("11", "Limitations & Future Work")

    pdf.section_title("11.1 Limitations")
    pdf.bullet("Convenience survey samples are not nationally representative of India's population.")
    pdf.bullet("The current survey results use 60 ILLUSTRATIVE SYNTHETIC responses, not real consumers; they demonstrate the workflow only.")
    pdf.bullet("Self-reported price sensitivity is not the same as observed price elasticity.")
    pdf.bullet("The SAM share (30%) and growth scenario CAGRs are assumptions, not measured values.")
    pdf.bullet("IBEF forecast values for 2025+ are published projections used as benchmarks, never as observed outcomes.")
    pdf.bullet("MoSPI HCES measures household consumption expenditure, not online transactions.")
    pdf.bullet("Only four reported total-market observations (2021-2024) exist: backtests have n=2 per model and the fitted CAGR interval is very wide (df=2).")
    pdf.bullet("Segment stability and permutation results describe the small synthetic sample only; they cannot establish that the clusters represent real market segments.")

    pdf.section_title("11.2 Future Work")
    pdf.bullet("Replace the illustrative synthetic sample with real consented responses across diverse Indian states and demographic groups, then re-run the full validation suite.")
    pdf.bullet("Validate scenario assumptions against additional industry reports and analyst forecasts.")
    pdf.bullet("Incorporate transaction data analysis for empirical purchasing pattern insights.")
    pdf.bullet("Extend the reported market series with more observed years to tighten CAGR confidence intervals and support longer backtests.")
    pdf.bullet("Add regional (state-level) analysis of e-commerce adoption and category preferences.")
    pdf.bullet("Compare additional offline forecasting models once enough observed annual data are available.")

    # =====================================================================
    #  12. REFERENCES
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("12", "References")

    refs = [
        ("IBEF (2025)", "India E-Commerce Infographic, August 2025.",
         "https://www.ibef.org/uploads/industry/Infrographics/large/e-Commerce-infographics-august-2025.pdf"),
        ("NITI Aayog (2026)", "Trade Watch Quarterly, Q2 FY 2025-26, July-September.",
         "https://niti.gov.in/sites/default/files/2026-02/Trade-Watch-Quarterly-July-September-Q2-FY-2025-26.pdf"),
        ("MoSPI", "Household Consumer Expenditure Survey (HCES).",
         "https://microdata.gov.in/NADA/index.php/catalog/CEXP"),
    ]
    for i, (author, title, url) in enumerate(refs, 1):
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(8, 6, f"[{i}]")
        pdf.cell(0, 6, f"{author}", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(8, 6, "")
        pdf.cell(0, 6, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Helvetica", "", 9)
        pdf.set_text_color(50, 100, 150)
        pdf.cell(8, 6, "")
        pdf.cell(0, 6, url, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(4)

    # =====================================================================
    #  13. STATISTICAL VALIDATION & INTERACTIVE DASHBOARD
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("13", "Statistical Validation & Interactive Dashboard")
    pdf.body_text(
        "This chapter reports the diagnostic outputs added to the project. Every table below is "
        "read from the generated CSV files when the report is built; if an output is not yet "
        "available, a short note is printed instead of failing."
    )

    pdf.section_title("13.1 Segmentation Validation")
    seg_rows = read_rows(OUT / "segment_validation.csv")
    if not seg_rows:
        not_generated(pdf, "outputs/segment_validation.csv")
    else:
        v = seg_rows[0]
        pdf.body_text(
            f"The selected k is the candidate with the highest silhouette score. Stability was "
            f"checked with {fmt(v.get('n_seeds'))} random seeds, "
            f"{fmt(v.get('n_bootstraps'))} bootstrap resamples at 80% size, and a permutation "
            f"test of {fmt(v.get('n_permutations'))} independent feature shuffles."
        )
        pdf.ensure_space(80)
        pdf.add_table(
            ["Diagnostic", "Value"],
            [
                ["Selected k", fmt(v.get("k_selected"))],
                ["Silhouette", num(v.get("silhouette"), 3)],
                ["Calinski-Harabasz", num(v.get("calinski_harabasz"), 2)],
                ["Davies-Bouldin", num(v.get("davies_bouldin"), 4)],
                ["Seed ARI (mean / min)",
                 num(v.get("seed_ari_mean"), 3) + " / " + num(v.get("seed_ari_min"), 3)],
                ["Bootstrap ARI (mean / p05)",
                 num(v.get("bootstrap_ari_mean"), 3) + " / " + num(v.get("bootstrap_ari_p05"), 3)],
                ["Silhouette observed / permuted",
                 num(v.get("observed_silhouette"), 3) + " / " + num(v.get("permuted_silhouette_mean"), 3)],
                ["Permutation p-value", num(v.get("p_value"), 4)],
                ["Respondents used", fmt(v.get("n_respondents"))],
            ],
            [86, 70],
        )
        sig = read_rows(OUT / "feature_significance.csv")
        if sig:
            pdf.body_text("Per-feature differences across the selected segments (Kruskal-Wallis):")
            pdf.ensure_space(20 + 7 * len(sig))
            pdf.add_table(
                ["Feature", "Kruskal H", "p-value", "Effect size (eta^2)"],
                [[fmt(r.get("feature")), num(r.get("kruskal_H"), 2),
                  ("<0.001" if r.get("p_value") not in (None, "")
                   and float(r["p_value"]) < 0.001 else num(r.get("p_value"), 3)),
                  num(r.get("eta_squared"), 3)] for r in sig],
                [68, 28, 28, 42],
            )
        pdf.body_text(
            "Adjusted Rand Index (ARI) measures agreement between partitions, with 1 meaning "
            "identical and 0 chance-level agreement. The permutation p-value is the proportion "
            "of shuffled-data solutions at least as separated as the observed one. These checks "
            "are computed on the bundled synthetic demonstration sample: they validate the "
            "pipeline, not a claim about real consumers."
        )

    pdf.section_title("13.2 Clustering Diagnostics")
    pdf.add_figure(FIG / "11_k_selection.png",
                   "Figure 11: silhouette and inertia across candidate k values")
    pdf.add_figure(FIG / "12_cluster_profiles.png",
                   "Figure 12: standardised influence-score means by cluster")

    profiles = read_rows(OUT / "cluster_profiles.csv")
    if not profiles:
        not_generated(pdf, "outputs/cluster_profiles.csv")
    else:
        pdf.body_text("Cluster profiles (mean influence scores on the original 1-5 ordinal scale):")
        pdf.ensure_space(20 + 7 * len(profiles))
        pdf.add_table(
            ["Cluster", "n", "Share %", "Price", "Disc", "EMI", "Exch", "Deliv", "Typical spend"],
            [[fmt(p.get("cluster")), fmt(p.get("n")), num(p.get("share_pct"), 1),
              num(p.get("price_sensitivity_mean"), 2), num(p.get("discount_importance_mean"), 2),
              num(p.get("emi_influence_mean"), 2), num(p.get("exchange_influence_mean"), 2),
              num(p.get("delivery_cost_influence_mean"), 2), fmt(p.get("typical_spend_band"))]
             for p in profiles],
            [18, 10, 16, 14, 14, 14, 14, 14, 34],
        )
        for p in profiles:
            pdf.bullet(
                f"{fmt(p.get('segment_label'))} - n={fmt(p.get('n'))}, "
                f"{num(p.get('share_pct'), 1)}% of respondents"
            )

    pdf.add_page()
    pdf.section_title("13.3 Forecasting Evaluation")
    comp = read_rows(OUT / "forecast_model_comparison.csv")
    if not comp:
        not_generated(pdf, "outputs/forecast_model_comparison.csv")
    else:
        pdf.body_text(
            "Rolling-origin backtest scorecard (each model is refitted on earlier years and "
            "asked to predict the next one):"
        )
        pdf.ensure_space(20 + 7 * len(comp))
        pdf.add_table(
            ["Model", "n", "MAE (US$bn)", "MAPE (%)", "IBEF MAPE (%)", "R2"],
            [[fmt(r.get("model")), fmt(r.get("backtest_n")),
              num(r.get("backtest_MAE_usd_bn"), 2), num(r.get("backtest_MAPE_pct"), 2),
              num(r.get("ibef_benchmark_MAPE_pct"), 2), num(r.get("in_sample_R2"), 3)]
             for r in comp],
            [58, 10, 26, 22, 28, 18],
        )
    pdf.add_figure(FIG / "14_forecast_backtest.png",
                   "Figure 14: fitted models, backtest predictions and MAPE by model")

    growth = read_rows(OUT / "growth_rate_benchmarks.csv")
    if not growth:
        not_generated(pdf, "outputs/growth_rate_benchmarks.csv")
    else:
        pdf.body_text("Growth-rate benchmarks (missing confidence bounds appear as n/a):")
        pdf.ensure_space(20 + 7 * len(growth))
        pdf.add_table(
            ["Benchmark", "Period", "CAGR (%)", "CI low (%)", "CI high (%)"],
            [[fmt(r.get("benchmark")), fmt(r.get("period")), num(r.get("cagr_pct"), 2),
              num(r.get("ci_low_pct"), 2), num(r.get("ci_high_pct"), 2)] for r in growth],
            [70, 38, 22, 22, 22],
        )
        fitted = next((r for r in growth
                       if "Reported total market" in fmt(r.get("benchmark"))), {})
        n_back = fmt(comp[0].get("backtest_n")) if comp else "n/a"
        pdf.body_text(
            "SMALL-SAMPLE CAVEAT: only four reported total-market observations (2021-2024) "
            f"exist, so each rolling-origin backtest has just {n_back} prediction(s) per model. "
            f"The fitted 2021-2024 CAGR is about {num(fitted.get('cagr_pct'), 1)}%, with a 95% "
            f"confidence interval of {num(fitted.get('ci_low_pct'), 1)}% to "
            f"{num(fitted.get('ci_high_pct'), 1)}% (t-based, df=2) - far too wide for planning. "
            "The 8%/12%/16% scenario rates remain illustrative assumptions, not estimates. "
            "IBEF's 2025-2035 figures are published forecasts used only as benchmarks, never as "
            "observed outcomes. These diagnostics are sanity checks, not strong statistical "
            "inference."
        )
    pdf.add_figure(FIG / "15_ibef_benchmark.png",
                   "Figure 15: model projections vs published IBEF forecasts (benchmarks, not outcomes)")

    pdf.section_title("13.4 Interactive Dashboard")
    if not (OUT / "dashboard.html").exists():
        not_generated(pdf, "outputs/dashboard.html")
    else:
        pdf.body_text(
            "outputs/dashboard.html is a single self-contained file with Plotly.js embedded, so "
            "it opens in any modern browser offline: no web server, no installation and no "
            "network connection are required. Its five tabs are Market Overview (reported and "
            "forecast series, category benchmark, TAM/SAM), Scenario Explorer (sliders for "
            "CAGR, SAM share and 2024 TAM), Consumer Segments (profiles, PCA scatter and k "
            "diagnostics), Statistical Validation (backtests, IBEF benchmarks and growth-rate "
            "comparisons) and Data & Methods (survey encoding, input notes and caveats)."
        )
        pdf.body_text(
            "The dashboard and this PDF are generated from the same CSV outputs, so figures and "
            "tables stay consistent. Because the survey sample is synthetic and the reported "
            "market series is short, the dashboard labels its findings as illustrative."
        )

    # ---- End matter ----
    pdf.ln(10)
    pdf.set_draw_color(60, 130, 100)
    pdf.set_line_width(0.4)
    pdf.line(10, pdf.get_y(), pdf.w - 10, pdf.get_y())
    pdf.ln(6)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, "End of Report", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 6, f"Generated on {date.today().strftime('%B %d, %Y')}", align="C")

    # ---- Save ----
    OUT.mkdir(parents=True, exist_ok=True)
    pdf.output(str(REPORT_PATH))
    print(f"\nReport saved: {REPORT_PATH}")
    print(f"Pages: {pdf.page_no()}")
    if sys.platform == "win32":
        os.startfile(str(REPORT_PATH))


if __name__ == "__main__":
    build_report()
