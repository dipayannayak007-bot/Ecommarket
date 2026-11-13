"""Reproducible market analysis for CNT-02.

Run from any working directory:
    python python/run_project.py

Outputs are written beneath python/reports/. No customer-level data is invented.
"""
from __future__ import annotations

from pathlib import Path
import html
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data" / "india_ecommerce_market.csv"
REPORT = ROOT / "reports"
FIG = REPORT / "figures"
TABLES = REPORT / "tables"


def load_market_data(path: Path = DATA) -> pd.DataFrame:
    """Load and validate the published benchmark dataset."""
    df = pd.read_csv(path)
    required = {"year", "market_value_usd_bn", "status", "market_scope", "source"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Market dataset is missing columns: {sorted(missing)}")
    if df[list(required)].isnull().any().any():
        raise ValueError("Market dataset contains missing required values.")
    if (pd.to_numeric(df["market_value_usd_bn"], errors="coerce") <= 0).any():
        raise ValueError("Market values must be positive numeric values.")
    df["year"] = pd.to_numeric(df["year"], errors="raise").astype(int)
    df["market_value_usd_bn"] = pd.to_numeric(
        df["market_value_usd_bn"], errors="raise"
    )
    return df


def calculate_adjacent_year_growth(total: pd.DataFrame) -> pd.DataFrame:
    """Calculate YoY growth only for consecutive calendar years.

    The source series has gaps (for example 2026 to 2030); those gaps must
    not be mislabeled as one-year growth.
    """
    result = total.sort_values("year").copy()
    year_gap = result["year"].diff()
    result["yoy_growth_percent"] = (
        result["market_value_usd_bn"].pct_change() * 100
    ).where(year_gap.eq(1))
    return result


def build_scenarios(base_tam: float = 27.0) -> pd.DataFrame:
    """Create explicit illustrative TAM/SAM scenarios, not official forecasts."""
    rows = []
    for label, cagr in [
        ("Conservative", 0.08),
        ("Base", 0.12),
        ("Optimistic", 0.16),
    ]:
        for year in range(2024, 2036):
            tam = base_tam * (1 + cagr) ** (year - 2024)
            rows.append({
                "year": year,
                "scenario": label,
                "assumed_cagr_percent": cagr * 100,
                "tam_usd_bn": tam,
                "sam_reachability_percent_assumption": 30.0,
                "illustrative_sam_usd_bn": tam * 0.30,
            })
    return pd.DataFrame(rows)


def save_figure(fig, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight")
    plt.close(fig)


def create_html_report(figures: list[Path], tables: list[Path]) -> None:
    """Create a self-contained index page referencing generated local assets."""
    image_sections = "".join(
        f'<section><h2>{html.escape(p.stem.replace("_", " ").title())}</h2>'
        f'<img src="figures/{html.escape(p.name)}" alt="{html.escape(p.stem)}">'
        f'</section>'
        for p in figures
    )
    table_links = "".join(
        f'<li><a href="tables/{html.escape(p.name)}">{html.escape(p.name)}</a></li>'
        for p in tables
    )
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>CNT-02 | India E-commerce Market Analysis</title>
<style>
body{{font:16px system-ui,sans-serif;max-width:1100px;margin:32px auto;padding:0 20px;color:#172033;line-height:1.55}}
img{{max-width:100%;height:auto;border:1px solid #dce2ea;border-radius:8px}}
section{{margin:30px 0}} a{{color:#145ca8}} .note{{padding:14px;background:#f2f5f9;border-radius:8px}}
</style></head><body>
<h1>India E-commerce Market Growth and Consumer Segmentation</h1>
<p class="note">This report is generated from published market benchmarks. Forecasts and
scenario assumptions are distinguished from reported values. No survey or transaction
observations are fabricated. Consumer segmentation is produced only when eligible
consented survey responses are supplied.</p>
<h2>Derived visual analysis</h2>{image_sections}
<h2>Downloadable analysis tables</h2><ul>{table_links}</ul>
<h2>Interpretation boundary</h2>
<p>Market size is not retailer revenue. The 8%, 12% and 16% growth rates and 30%
SAM reachability are illustrative assumptions, not official forecasts or measured shares.
The available benchmark series has gaps; annual growth is shown only for adjacent years.</p>
</body></html>"""
    (REPORT / "Project_Report.html").write_text(page, encoding="utf-8")


def main() -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)
    df = load_market_data()
    total = df[df.market_scope.eq("India total e-commerce")].copy()
    if total.empty:
        raise ValueError("No India total e-commerce rows found in the dataset.")
    total = calculate_adjacent_year_growth(total)
    total.to_csv(TABLES / "india_market_growth.csv", index=False)

    scenarios = build_scenarios()
    scenarios.to_csv(TABLES / "tam_sam_scenarios.csv", index=False)

    sensitivity = []
    for rate in [0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18]:
        for share in [0.20, 0.25, 0.30, 0.35, 0.40]:
            tam_2030 = 27 * (1 + rate) ** 6
            sensitivity.append({
                "growth_percent_assumption": rate * 100,
                "sam_reachability_percent_assumption": share * 100,
                "tam_2030_usd_bn": tam_2030,
                "illustrative_sam_2030_usd_bn": tam_2030 * share,
            })
    sensitivity_df = pd.DataFrame(sensitivity)
    sensitivity_df.to_csv(TABLES / "sensitivity_2030.csv", index=False)

    figures: list[Path] = []
    fig, ax = plt.subplots(figsize=(9, 5))
    for status, style, label in [
        ("Reported", "-", "Reported"),
        ("Forecast", "--", "Published forecast"),
    ]:
        part = total[total.status.eq(status)]
        ax.plot(part.year, part.market_value_usd_bn, marker="o",
                linestyle=style, label=label)
    ax.set(title="India e-commerce market: reported values and forecasts",
           xlabel="Year", ylabel="USD billion")
    ax.legend()
    path = FIG / "01_market_growth.png"
    save_figure(fig, path); figures.append(path)

    adjacent = total.dropna(subset=["yoy_growth_percent"])
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(adjacent.year.astype(str), adjacent.yoy_growth_percent)
    ax.set(title="Year-on-year growth (consecutive years only)",
           xlabel="Year", ylabel="Growth (%)")
    path = FIG / "02_annual_growth.png"
    save_figure(fig, path); figures.append(path)

    categories = df[
        df.year.eq(2024) & ~df.market_scope.eq("India total e-commerce")
    ]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.bar(categories.market_scope, categories.market_value_usd_bn)
    ax.tick_params(axis="x", rotation=15)
    ax.set(title="Selected 2024 online category benchmarks",
           xlabel="Category", ylabel="USD billion")
    path = FIG / "03_category_benchmarks.png"
    save_figure(fig, path); figures.append(path)

    fig, ax = plt.subplots(figsize=(9, 5))
    for label, group in scenarios.groupby("scenario"):
        ax.plot(group.year, group.tam_usd_bn, label=label)
    ax.set(title="Illustrative electronics and appliances TAM scenarios",
           xlabel="Year", ylabel="USD billion")
    ax.legend()
    path = FIG / "04_tam_scenarios.png"
    save_figure(fig, path); figures.append(path)

    base = scenarios[scenarios.scenario.eq("Base")]
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(base.year, base.tam_usd_bn, label="TAM")
    ax.plot(base.year, base.illustrative_sam_usd_bn,
            label="Illustrative SAM (30% assumption)")
    ax.set(title="Base-case TAM and illustrative SAM",
           xlabel="Year", ylabel="USD billion")
    ax.legend()
    path = FIG / "05_tam_sam.png"
    save_figure(fig, path); figures.append(path)

    pivot = sensitivity_df.pivot(
        index="growth_percent_assumption",
        columns="sam_reachability_percent_assumption",
        values="illustrative_sam_2030_usd_bn",
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    heat = ax.imshow(pivot, aspect="auto", origin="lower")
    ax.set_xticks(range(len(pivot.columns)), [f"{x:g}%" for x in pivot.columns])
    ax.set_yticks(range(len(pivot.index)), [f"{x:g}%" for x in pivot.index])
    ax.set(xlabel="SAM reachability assumption",
           ylabel="Annual growth assumption",
           title="2030 illustrative SAM sensitivity (USD bn)")
    fig.colorbar(heat, ax=ax, label="USD billion")
    path = FIG / "06_sensitivity_heatmap.png"
    save_figure(fig, path); figures.append(path)

    tables = sorted(TABLES.glob("*.csv"))
    create_html_report(figures, tables)
    print(f"Created {len(figures)} PNG figures and {len(tables)} CSV tables.")
    print(f"HTML report: {REPORT / 'Project_Report.html'}")
    print("Customer segmentation is a separate, data-gated step:")
    print("python segment_consumers.py --input data/survey_responses.csv")


if __name__ == "__main__":
    main()
