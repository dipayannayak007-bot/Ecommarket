#!/usr/bin/env python3
"""CNT-02 India E-Commerce Market Growth and Consumer Segmentation.
Run: python run_project.py
No internet connection or API access is used at runtime.
"""
from pathlib import Path
import argparse
import os
import sys
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FIG = OUT / "figures"


def open_image(path):
    """Open an image file with the default Windows viewer."""
    if sys.platform == "win32" and path.exists():
        try:
            os.startfile(str(path))
        except Exception:
            pass


def setup():
    FIG.mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)


def market_data():
    return pd.read_csv(DATA / "india_ecommerce_market.csv")


def save_market_trend(df):
    d = df[df.market_scope.eq("India total e-commerce")].sort_values("year")
    fig, ax = plt.subplots(figsize=(10, 6))
    for status, part in d.groupby("status"):
        ax.plot(part.year, part.market_value_usd_bn, marker="o", lw=2, label=status)
    ax.set(title="India E-Commerce Market: Reported Values and Forecasts",
           xlabel="Year", ylabel="Market Value (US$ billion)")
    ax.grid(alpha=.25); ax.legend()
    path = FIG / "01_india_market_trend.png"
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)
    open_image(path)
    print(f"  -> Generated: {path.name}")


def save_category_chart(df):
    d = df[df.market_scope.isin([
        "India online electronics and appliances",
        "India online smartphones (separate category)"
    ])].copy()
    labels = {
        "India online electronics and appliances": "Electronics & appliances",
        "India online smartphones (separate category)": "Smartphones"
    }
    d["label"] = d.market_scope.map(labels)
    fig, ax = plt.subplots(figsize=(9, 5.5))
    bars = ax.barh(d.label, d.market_value_usd_bn, color="#39856A")
    ax.bar_label(bars, labels=[f"${v:.0f}bn" for v in d.market_value_usd_bn], padding=5)
    ax.set(title="Selected Online Electronics Categories in India (2024)",
           xlabel="Market Value (US$ billion)")
    ax.set_xlim(0, max(d.market_value_usd_bn) * 1.25); ax.grid(axis="x", alpha=.2)
    path = FIG / "02_category_benchmark.png"
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)
    open_image(path)
    print(f"  -> Generated: {path.name}")


def scenario_table(tam, sam_share):
    rows = []
    for name, rate in [("Conservative", .08), ("Base", .12), ("Optimistic", .16)]:
        for year in range(2024, 2031):
            value = tam * (1 + rate) ** (year - 2024)
            rows.append({"year": year, "scenario": name, "cagr": rate,
                         "tam_usd_bn": round(value, 2),
                         "illustrative_sam_usd_bn": round(value * sam_share, 2)})
    d = pd.DataFrame(rows)
    d.to_csv(OUT / "electronics_scenario_forecast.csv", index=False)
    return d


def save_scenario_chart(d):
    fig, ax = plt.subplots(figsize=(10, 6))
    for name, part in d.groupby("scenario"):
        ax.plot(part.year, part.tam_usd_bn, marker="o", lw=2, label=f"{name} ({part.cagr.iloc[0]:.0%})")
    ax.set(title="Electronics & Appliances: Illustrative Growth Scenarios (2024-2030)",
           xlabel="Year", ylabel="Projected TAM (US$ billion)")
    ax.set_xticks(range(2024, 2031)); ax.grid(alpha=.25); ax.legend(title="Scenario")
    path = FIG / "03_tam_scenarios.png"
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)
    open_image(path)
    print(f"  -> Generated: {path.name}")


def save_tam_sam(tam, share):
    labels, values = ["TAM", "Illustrative SAM"], [tam, tam * share]
    fig, ax = plt.subplots(figsize=(8, 5.5))
    bars = ax.bar(labels, values, color=["#4C78A8", "#F2A541"], width=.58)
    ax.bar_label(bars, labels=[f"${v:.1f}bn" for v in values], padding=5)
    ax.set(title="2024 India Electronics & Appliances Market Sizing",
           ylabel="Market Value (US$ billion)")
    ax.text(.5, .94, f"SAM assumes {share:.0%} reachable share",
            transform=ax.transAxes, ha="center", va="top", fontsize=9)
    ax.set_ylim(0, tam * 1.25); ax.grid(axis="y", alpha=.2)
    path = FIG / "04_tam_sam.png"
    fig.tight_layout(); fig.savefig(path, dpi=220); plt.close(fig)
    open_image(path)
    print(f"  -> Generated: {path.name}")


def statistical_validation(df_market):
    """Perform statistical validation, regression metrics, and CAGR evaluation."""
    total_mkt = df_market[df_market.market_scope.eq("India total e-commerce")].copy()
    reported = total_mkt[total_mkt.status.eq("Reported")].sort_values("year")
    forecast = total_mkt[total_mkt.status.eq("Forecast")].sort_values("year")
    
    # Historical CAGR (2021-2024)
    v_start, v_end = reported.iloc[0].market_value_usd_bn, reported.iloc[-1].market_value_usd_bn
    years_hist = reported.iloc[-1].year - reported.iloc[0].year
    hist_cagr = (v_end / v_start) ** (1 / years_hist) - 1
    
    # Exponential model log(y) = a * year + b
    x_hist = reported.year.values
    y_hist = reported.market_value_usd_bn.values
    coeffs = np.polyfit(x_hist, np.log(y_hist), 1)
    y_pred_hist = np.exp(coeffs[1] + coeffs[0] * x_hist)
    
    # R2 and RMSE on historical curve
    ss_res = np.sum((y_hist - y_pred_hist) ** 2)
    ss_tot = np.sum((y_hist - np.mean(y_hist)) ** 2)
    r2_hist = 1 - (ss_res / ss_tot)
    rmse_hist = np.sqrt(np.mean((y_hist - y_pred_hist) ** 2))
    mape_hist = np.mean(np.abs((y_hist - y_pred_hist) / y_hist)) * 100
    
    # Projected 2030 by pure trend extrapolation vs IBEF forecast
    extrapolated_2030 = np.exp(coeffs[1] + coeffs[0] * 2030)
    ibef_2030 = forecast[forecast.year.eq(2030)].market_value_usd_bn.values[0] if 2030 in forecast.year.values else np.nan
    
    val_df = pd.DataFrame([{
        "Metric": "Historical CAGR (2021-2024)",
        "Value": f"{hist_cagr:.2%}",
        "Interpretation": "Rapid post-pandemic expansion phase"
    }, {
        "Metric": "Log-Linear Model Fit R²",
        "Value": f"{r2_hist:.4f}",
        "Interpretation": "Strong exponential fit on reported values"
    }, {
        "Metric": "Historical MAPE",
        "Value": f"{mape_hist:.2f}%",
        "Interpretation": "Average percentage tracking error"
    }, {
        "Metric": "Historical RMSE",
        "Value": f"US$ {rmse_hist:.2f} bn",
        "Interpretation": "Root mean squared deviation"
    }, {
        "Metric": "Extrapolated 2030 (Pure Trend)",
        "Value": f"US$ {extrapolated_2030:.1f} bn",
        "Interpretation": "Unconstrained continuation of historical momentum"
    }, {
        "Metric": "IBEF Forecast 2030",
        "Value": f"US$ {ibef_2030:.1f} bn",
        "Interpretation": "Official consensus forecast incorporating maturity deceleration"
    }])
    
    val_df.to_csv(OUT / "statistical_forecast_validation.csv", index=False)
    print("  -> Generated: statistical_forecast_validation.csv")
    return val_df


def analyse_transactions():
    path = DATA / "transactions.csv"
    if not path.exists() or path.stat().st_size == 0:
        print("No transaction data supplied: skipping empirical transaction charts.")
        return
    d = pd.read_csv(path)
    if not {"quantity", "unit_price_inr"}.issubset(d.columns):
        warnings.warn("transactions.csv requires quantity and unit_price_inr.")
        return
    d["gross_value_inr"] = pd.to_numeric(d.quantity, errors="coerce") * pd.to_numeric(d.unit_price_inr, errors="coerce")
    discount = pd.to_numeric(d.discount_inr, errors="coerce").fillna(0) if "discount_inr" in d else 0
    d["net_value_inr"] = d.gross_value_inr - discount
    d = d.replace([np.inf, -np.inf], np.nan).dropna(subset=["net_value_inr"])
    d = d[d.net_value_inr >= 0]
    if d.empty:
        print("No valid transaction values.")
        return
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.hist(d.net_value_inr, bins=30, color="#4C78A8", edgecolor="white")
    ax.set(title="Distribution of Transaction Values", xlabel="Net transaction value (INR)", ylabel="Records")
    ax.grid(axis="y", alpha=.2); fig.tight_layout()
    img_path = FIG / "05_transaction_value_histogram.png"
    fig.savefig(img_path, dpi=220); plt.close(fig)
    open_image(img_path)
    if "category" in d:
        bycat = d.groupby("category").net_value_inr.sum().sort_values()
        fig, ax = plt.subplots(figsize=(9, 6))
        bycat.plot(kind="barh", ax=ax, color="#39856A")
        ax.set(title="Net Sales by Category", xlabel="Net sales (INR)", ylabel="")
        img_path2 = FIG / "06_transaction_sales_by_category.png"
        fig.tight_layout(); fig.savefig(img_path2, dpi=220); plt.close(fig)
        open_image(img_path2)
    pd.DataFrame([{
        "records": len(d),
        "orders": d.order_id.nunique() if "order_id" in d else np.nan,
        "customers": d.customer_id.nunique() if "customer_id" in d else np.nan,
        "net_sales_inr": d.net_value_inr.sum()
    }]).to_csv(OUT / "transaction_summary.csv", index=False)


def analyse_survey():
    # Resolve file name (accept either survey_responses.csv or sample_survey_responses.csv)
    path = DATA / "survey_responses.csv"
    if not path.exists() or path.stat().st_size == 0:
        path = DATA / "sample_survey_responses.csv"
    
    if not path.exists() or path.stat().st_size == 0:
        print("No survey responses supplied: skipping empirical consumer charts.")
        return

    print(f"Reading survey responses from: {path.name}")
    d = pd.read_csv(path)
    
    # 1. Descriptive Survey Visualisations
    charts = [
        ("purchase_frequency_12m", "07_purchase_frequency.png", "Online Purchase Frequency (Last 12 Months)", "#E39C37"),
        ("preferred_category", "08_preferred_category.png", "Preferred Online Shopping Category", "#39856A"),
        ("spend_band_inr", "09_spending_bands.png", "Respondent Spending Bands (INR)", "#8064A2"),
        ("price_sensitivity", "10_price_sensitivity.png", "Self-Reported Price Sensitivity", "#4C78A8"),
    ]
    for col, filename, title, color in charts:
        if col not in d:
            continue
        counts = d[col].dropna().astype(str).str.strip()
        counts = counts[counts.ne("")].value_counts()
        if counts.empty:
            continue
        fig, ax = plt.subplots(figsize=(9, max(4.5, .45 * len(counts))))
        counts.sort_values().plot(kind="barh", ax=ax, color=color)
        ax.set(title=title, xlabel="Respondents", ylabel="")
        img_path = FIG / filename
        fig.tight_layout(); fig.savefig(img_path, dpi=220); plt.close(fig)
        open_image(img_path)
        print(f"  -> Generated: {filename}")

    # 2. Ordinal-to-Numeric Likert Mapping for K-Means Clustering
    influence_map = {
        "not at all": 1,
        "not applicable": 1,
        "not eligible / unsure": 1,
        "a little": 2,
        "somewhat": 3,
        "a lot": 4
    }
    sensitivity_map = {
        "not at all": 1,
        "slightly": 2,
        "moderately": 3,
        "very": 4,
        "extremely": 5
    }

    numeric_df = pd.DataFrame(index=d.index)

    # Encode discount_importance (already 1-5 or text)
    if "discount_importance" in d:
        numeric_df["discount_importance"] = pd.to_numeric(d["discount_importance"], errors="coerce").fillna(3)

    # Encode price_sensitivity
    if "price_sensitivity" in d:
        numeric_df["price_sensitivity_score"] = d["price_sensitivity"].astype(str).str.lower().str.strip().map(sensitivity_map).fillna(3)

    # Encode EMI, Exchange, Delivery Cost influences
    for col, new_name in [("emi_influence", "emi_influence_score"),
                          ("exchange_influence", "exchange_influence_score"),
                          ("delivery_cost_influence", "delivery_cost_influence_score")]:
        if col in d:
            numeric_df[new_name] = d[col].astype(str).str.lower().str.strip().map(influence_map).fillna(2)
        elif new_name in d:
            numeric_df[new_name] = pd.to_numeric(d[new_name], errors="coerce").fillna(2)

    features = [c for c in ["discount_importance", "price_sensitivity_score", "emi_influence_score",
                            "exchange_influence_score", "delivery_cost_influence_score"] if c in numeric_df]

    if len(features) >= 3 and len(numeric_df.dropna()) >= 10:
        try:
            from sklearn.cluster import KMeans
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import silhouette_score

            X = numeric_df[features].dropna()
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)

            k = 3
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            clusters = kmeans.fit_predict(X_scaled)
            sil_score = silhouette_score(X_scaled, clusters)

            cluster_labels = {
                0: "Value & Discount Seekers",
                1: "Financing & Offer Driven",
                2: "Convenience & Premium Shoppers"
            }

            result = d.loc[X.index].copy()
            result["cluster_id"] = clusters + 1
            result["cluster_name"] = [cluster_labels.get(c, f"Segment {c+1}") for c in clusters]
            for f in features:
                result[f] = X[f]

            result.to_csv(OUT / "exploratory_consumer_segments.csv", index=False)
            print(f"  -> Generated: exploratory_consumer_segments.csv (Silhouette Score: {sil_score:.3f})")

            # Cluster Profile Summary
            profile = result.groupby("cluster_name")[features].mean().round(2)
            profile["respondent_count"] = result.groupby("cluster_name").size()
            profile.to_csv(OUT / "segment_profile_summary.csv")
            print("  -> Generated: segment_profile_summary.csv")

            # Visualize Segment Profiles Radar / Bar Chart
            fig, ax = plt.subplots(figsize=(10, 6))
            profile[features].T.plot(kind="bar", ax=ax, width=0.75, colormap="viridis")
            ax.set(title=f"Consumer Segmentation Profiles (K={k}, Silhouette={sil_score:.2f})",
                   ylabel="Average Score (1 to 4/5)", xlabel="Influence Dimensions")
            ax.set_xticklabels([f.replace("_", " ").title() for f in features], rotation=25, ha="right")
            ax.grid(axis="y", alpha=0.3)
            ax.legend(title="Segment")
            fig.tight_layout()
            cluster_img = FIG / "11_consumer_clusters.png"
            fig.savefig(cluster_img, dpi=220); plt.close(fig)
            open_image(cluster_img)
            print(f"  -> Generated: {cluster_img.name}")

        except ImportError:
            print("scikit-learn not available: skipping clustering.")


def main():
    parser = argparse.ArgumentParser(description="Run CNT-02 offline Python analysis.")
    parser.add_argument("--tam", type=float, default=27.0, help="2024 category TAM in US$bn")
    parser.add_argument("--sam-share", type=float, default=.30, help="Illustrative SAM share (0 to 1)")
    args = parser.parse_args()
    if args.tam <= 0 or not 0 <= args.sam_share <= 1:
        parser.error("--tam must be positive and --sam-share must be between 0 and 1")
    setup()
    df = market_data()
    save_market_trend(df); save_category_chart(df)
    scenarios = scenario_table(args.tam, args.sam_share)
    save_scenario_chart(scenarios); save_tam_sam(args.tam, args.sam_share)
    statistical_validation(df)
    analyse_transactions()
    analyse_survey()
    print("\nAnalysis complete.")
    print(f"Charts saved in: {FIG}")
    print(f"Outputs saved in: {OUT}")

if __name__ == "__main__":
    main()
