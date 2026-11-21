#!/usr/bin/env python3
"""Statistical evaluation of the CNT-02 market projections.

The original project produced illustrative CAGR scenarios but no evaluation.
This module adds honest, small-sample diagnostics:

* rolling-origin backtests on the four reported total-market observations;
* comparison against the published IBEF forecast points (benchmarks, not outcomes);
* residual-based 95% prediction intervals for the fitted log-linear trend;
* implied CAGRs with analytic confidence intervals;
* a CAGR sensitivity grid used by the interactive dashboard.

With only four reported observations these are sanity checks, NOT a basis for
strong statistical inference. Every output states its sample size.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FIG = OUT / "figures"

COLOURS = {
    "CAGR (log-linear)": "#39856A",
    "Linear trend": "#4C78A8",
    "Holt exponential smoothing": "#E39C37",
    "Naive (last value)": "#8064A2",
}


def _metrics(actual, predicted) -> dict:
    actual = np.asarray(actual, dtype=float)
    predicted = np.asarray(predicted, dtype=float)
    errors = actual - predicted
    mape_terms = np.abs(errors / actual) * 100
    smape_terms = 200 * np.abs(errors) / (np.abs(actual) + np.abs(predicted))
    return {
        "n": int(len(actual)),
        "MAE": round(float(np.mean(np.abs(errors))), 3),
        "RMSE": round(float(np.sqrt(np.mean(errors ** 2))), 3),
        "MAPE_pct": round(float(np.mean(mape_terms)), 2),
        "sMAPE_pct": round(float(np.mean(smape_terms)), 2),
    }


def _fit_models(years, values) -> dict:
    """Fit four candidate models and return year -> prediction callables."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    t = years - years[0]

    slope, intercept = np.polyfit(t, np.log(values), 1)
    lin_slope, lin_intercept = np.polyfit(t, values, 1)

    # Holt's linear method with a small grid search for alpha / beta.
    best = None
    for alpha in np.arange(0.10, 1.0, 0.05):
        for beta in np.arange(0.10, 1.0, 0.05):
            level, trend, sse = values[0], values[1] - values[0], 0.0
            for i in range(2, len(values)):
                forecast = level + trend
                sse += (values[i] - forecast) ** 2
                new_level = alpha * values[i] + (1 - alpha) * forecast
                trend = beta * (new_level - level) + (1 - beta) * trend
                level = new_level
            if best is None or sse < best[0]:
                best = (sse, alpha, beta, level, trend)
    _, alpha, beta, holt_level, holt_trend = best

    return {
        "CAGR (log-linear)": (lambda y: float(np.exp(intercept + slope * (y - years[0])))),
        "Linear trend": (lambda y: float(lin_intercept + lin_slope * (y - years[0]))),
        "Holt exponential smoothing": (
            lambda y: float(holt_level + holt_trend * (y - years[0] - (len(values) - 1)))
        ),
        "Naive (last value)": (lambda y: float(values[-1])),
    }


def _cagr_details(years, values) -> dict:
    """Analytic 95% CI for the fitted log-linear growth rate."""
    years = np.asarray(years, dtype=float)
    values = np.asarray(values, dtype=float)
    t = years - years[0]
    slope, intercept = np.polyfit(t, np.log(values), 1)
    n = len(values)
    dof = n - 2
    residuals = np.log(values) - (intercept + slope * t)
    sigma2 = float(np.sum(residuals ** 2) / dof)
    sxx = float(np.sum((t - t.mean()) ** 2))
    se_slope = np.sqrt(sigma2 / sxx)
    tcrit = float(stats.t.ppf(0.975, dof))
    return {
        "cagr_pct": float((np.exp(slope) - 1) * 100),
        "ci_low_pct": float((np.exp(slope - tcrit * se_slope) - 1) * 100),
        "ci_high_pct": float((np.exp(slope + tcrit * se_slope) - 1) * 100),
        "residual_sd": float(np.sqrt(sigma2)),
        "tcrit": tcrit,
        "sigma2": sigma2,
        "sxx": sxx,
        "t_mean": float(t.mean()),
        "dof": dof,
        "n": n,
        "slope": float(slope),
        "intercept": float(intercept),
        "base_year": float(years[0]),
    }


def _prediction_intervals(details: dict, target_years) -> pd.DataFrame:
    rows = []
    for year in target_years:
        t = year - details["base_year"]
        point = float(np.exp(details["intercept"] + details["slope"] * t))
        se = np.sqrt(details["sigma2"] * (
            1 + 1 / details["n"] + (t - details["t_mean"]) ** 2 / details["sxx"]
        ))
        margin = details["tcrit"] * se
        rows.append({
            "year": int(year),
            "cagr_point_estimate_usd_bn": round(point, 2),
            "pi95_low_usd_bn": round(float(np.exp(np.log(point) - margin)), 2),
            "pi95_high_usd_bn": round(float(np.exp(np.log(point) + margin)), 2),
        })
    return pd.DataFrame(rows)


def _load_market() -> pd.DataFrame:
    return pd.read_csv(DATA / "india_ecommerce_market.csv")


def _save_figures(reported: pd.DataFrame, ibef: pd.DataFrame,
                  backtest: pd.DataFrame, comparison: pd.DataFrame,
                  intervals: pd.DataFrame, open_image) -> None:
    FIG.mkdir(parents=True, exist_ok=True)
    years = reported.year.to_numpy(dtype=float)
    values = reported.market_value_usd_bn.to_numpy(dtype=float)
    models = _fit_models(years, values)

    # Figure 14: in-sample fit + rolling-origin backtest points.
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(10, 9), sharex=True,
                                  gridspec_kw={"height_ratios": [3, 1.4]})
    ax.plot(years, values, "o-", color="black", lw=2.2, label="IBEF reported", zorder=5)
    grid = np.linspace(years.min(), years.max(), 100)
    for name, predict in models.items():
        ax.plot(grid, [predict(y) for y in grid], lw=1.6, label=name, alpha=.9)
    for name, part in backtest.groupby("model"):
        ax.scatter(part.year, part.predicted_usd_bn, marker="x", s=95, lw=2,
                   color=COLOURS[name], zorder=6)
    ax.set(ylabel="Market value (US$ billion)",
           title="Reported total market: fitted models (lines) and backtest predictions (x)")
    ax.grid(alpha=.25); ax.legend(fontsize=8)

    ordered = comparison.sort_values("backtest_MAPE_pct")
    ax2.barh(ordered.model, ordered.backtest_MAPE_pct,
             color=[COLOURS[name] for name in ordered.model])
    ax2.set(xlabel="Backtest MAPE (%)", title="Rolling-origin backtest error (n=2 per model)")
    ax2.grid(axis="x", alpha=.25); ax2.invert_yaxis()
    fig.tight_layout()
    path = FIG / "14_forecast_backtest.png"
    fig.savefig(path, dpi=200); plt.close(fig); open_image(path)

    # Figure 15: projections versus the published IBEF forecast points.
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.fill_between(intervals.year, intervals.pi95_low_usd_bn,
                    intervals.pi95_high_usd_bn, color="#39856A", alpha=.15,
                    label="95% prediction interval (fitted trend)")
    ax.plot(intervals.year, intervals.cagr_point_estimate_usd_bn, "--",
            color="#39856A", label="Fitted CAGR trend")
    ax.plot(ibef.year, ibef.market_value_usd_bn, "o-", color="black", lw=2,
            label="IBEF published forecast (benchmark)")
    for name, predict in models.items():
        ax.plot(intervals.year, [predict(y) for y in intervals.year], lw=1.4,
                alpha=.85, label=name)
    ax.set(title="Model projections vs published forecasts (2025-2035)",
           xlabel="Year", ylabel="Market value (US$ billion)")
    ax.grid(alpha=.25); ax.legend(fontsize=8)
    fig.tight_layout()
    path = FIG / "15_ibef_benchmark.png"
    fig.savefig(path, dpi=200); plt.close(fig); open_image(path)


def run(tam: float = 27.0, sam_share: float = 0.30, open_image=None) -> dict:
    """Run all forecast diagnostics, write CSVs/figures, return a summary dict."""
    if open_image is None:
        open_image = lambda _path: None

    market = _load_market()
    reported = market[market.status.str.contains("Reported", case=False, na=False) &
                      market.market_scope.eq("India total e-commerce")].sort_values("year")
    ibef = market[market.status.str.contains("Forecast", case=False, na=False) &
                  market.market_scope.eq("India total e-commerce")].sort_values("year")
    if len(reported) < 4 or len(ibef) < 1:
        raise ValueError("Need at least 4 reported and 1 forecast total-market observations.")

    years = reported.year.to_numpy(dtype=float)
    values = reported.market_value_usd_bn.to_numpy(dtype=float)
    details = _cagr_details(years, values)

    # --- rolling-origin backtest (train on earlier years, predict next year) ---
    backtest_rows = []
    for index in range(2, len(years)):
        train_models = _fit_models(years[:index], values[:index])
        for name, predict in train_models.items():
            prediction = float(predict(years[index]))
            error = float(values[index] - prediction)
            backtest_rows.append({
                "year": int(years[index]),
                "model": name,
                "actual_usd_bn": float(values[index]),
                "predicted_usd_bn": round(prediction, 3),
                "error_usd_bn": round(error, 3),
                "abs_error_usd_bn": round(abs(error), 3),
                "ape_pct": round(abs(error / values[index]) * 100, 2),
                "training_years": int(index),
            })
    backtest = pd.DataFrame(backtest_rows)
    backtest.to_csv(OUT / "forecast_backtest.csv", index=False)

    # --- benchmark against the published IBEF forecast points ---
    full_models = _fit_models(years, values)
    benchmark_rows = []
    for _, row in ibef.iterrows():
        for name, predict in full_models.items():
            prediction = float(predict(float(row.year)))
            benchmark_rows.append({
                "year": int(row.year),
                "model": name,
                "ibef_published_usd_bn": float(row.market_value_usd_bn),
                "model_projection_usd_bn": round(prediction, 3),
                "difference_usd_bn": round(prediction - float(row.market_value_usd_bn), 3),
                "ape_pct": round(abs(prediction - float(row.market_value_usd_bn))
                                 / float(row.market_value_usd_bn) * 100, 2),
            })
    benchmark = pd.DataFrame(benchmark_rows)
    benchmark.to_csv(OUT / "forecast_benchmark.csv", index=False)

    # --- model scorecard ---
    fitted = {name: np.array([predict(y) for y in years])
              for name, predict in full_models.items()}
    sst = float(np.sum((values - values.mean()) ** 2))
    comparisons = []
    for name in full_models:
        back = _metrics(backtest.loc[backtest.model.eq(name), "actual_usd_bn"],
                        backtest.loc[backtest.model.eq(name), "predicted_usd_bn"])
        bench = _metrics(benchmark.loc[benchmark.model.eq(name), "ibef_published_usd_bn"],
                         benchmark.loc[benchmark.model.eq(name), "model_projection_usd_bn"])
        fit_values = np.asarray(list(fitted[name]), dtype=float)
        comparisons.append({
            "model": name,
            "backtest_n": back["n"],
            "backtest_MAE_usd_bn": back["MAE"],
            "backtest_RMSE_usd_bn": back["RMSE"],
            "backtest_MAPE_pct": back["MAPE_pct"],
            "ibef_benchmark_n": bench["n"],
            "ibef_benchmark_MAE_usd_bn": bench["MAE"],
            "ibef_benchmark_MAPE_pct": bench["MAPE_pct"],
            "in_sample_R2": round(float(1 - np.sum((values - fit_values) ** 2) / sst), 4),
        })
    comparison = pd.DataFrame(comparisons)
    comparison.to_csv(OUT / "forecast_model_comparison.csv", index=False)

    # --- implied growth-rate benchmarks ---
    def implied(start, end, years_elapsed):
        return ((end / start) ** (1 / years_elapsed) - 1) * 100

    base_value = float(values[-1])
    base_year = int(years[-1])

    def ibef_value(year):
        match = ibef.loc[ibef.year.eq(year), "market_value_usd_bn"]
        return float(match.iloc[0]) if not match.empty else np.nan

    growth_rows = [
        {"benchmark": f"Reported total market {int(years[0])}-{base_year} (fitted)",
         "period": f"{int(years[0])}-{base_year}",
         "cagr_pct": round(details["cagr_pct"], 2),
         "ci_low_pct": round(details["ci_low_pct"], 2),
         "ci_high_pct": round(details["ci_high_pct"], 2),
         "note": f"{len(values)} reported points; analytic t-based CI, df={details['dof']}"},
        {"benchmark": "IBEF published forecast 2024-2030",
         "period": "2024-2030",
         "cagr_pct": round(implied(base_value, ibef_value(2030), 2030 - base_year), 2),
         "ci_low_pct": np.nan, "ci_high_pct": np.nan,
         "note": "Published forecast, not an observed outcome"},
        {"benchmark": "IBEF published forecast 2024-2035",
         "period": "2024-2035",
         "cagr_pct": round(implied(base_value, ibef_value(2035), 2035 - base_year), 2),
         "ci_low_pct": np.nan, "ci_high_pct": np.nan,
         "note": "Published forecast, not an observed outcome"},
    ]
    for label, rate in [("Conservative scenario", 8.0), ("Base scenario", 12.0),
                        ("Optimistic scenario", 16.0)]:
        growth_rows.append({
            "benchmark": label, "period": "2024-2030 (assumption)",
            "cagr_pct": rate, "ci_low_pct": np.nan, "ci_high_pct": np.nan,
            "note": "Illustrative input, not estimated from data",
        })
    growth = pd.DataFrame(growth_rows)
    growth.to_csv(OUT / "growth_rate_benchmarks.csv", index=False)

    # --- prediction intervals and CAGR sensitivity grid ---
    target_years = sorted(set(ibef.year.tolist()) | set(range(2025, 2031)))
    intervals = _prediction_intervals(details, target_years)
    published = dict(zip(ibef.year, ibef.market_value_usd_bn))
    intervals["ibef_published_usd_bn"] = intervals.year.map(published)
    intervals.to_csv(OUT / "forecast_prediction_intervals.csv", index=False)

    sensitivity_rows = []
    for rate in [6, 8, 10, 12, 14, 16, 18, 20, 22, 24]:
        value = tam * (1 + rate / 100) ** 6
        sensitivity_rows.append({
            "cagr_pct": rate,
            "tam_2030_usd_bn": round(float(value), 2),
            "sam_2030_usd_bn": round(float(value * sam_share), 2),
            "sam_share": sam_share,
        })
    sensitivity = pd.DataFrame(sensitivity_rows)
    sensitivity.to_csv(OUT / "cagr_sensitivity.csv", index=False)

    _save_figures(reported, ibef, backtest, comparison, intervals, open_image)

    return {
        "reported_years": [int(y) for y in years],
        "reported_values": [float(v) for v in values],
        "ibef_forecasts": ibef[["year", "market_value_usd_bn"]]
            .rename(columns={"market_value_usd_bn": "value"}).to_dict(orient="records"),
        "growth_rate_benchmarks": growth.to_dict(orient="records"),
        "model_comparison": comparison.to_dict(orient="records"),
        "backtest": backtest.to_dict(orient="records"),
        "benchmark": benchmark.to_dict(orient="records"),
        "prediction_intervals": intervals.to_dict(orient="records"),
        "cagr_sensitivity": sensitivity.to_dict(orient="records"),
        "fitted_cagr_pct": round(details["cagr_pct"], 2),
        "fitted_cagr_ci": [round(details["ci_low_pct"], 2),
                           round(details["ci_high_pct"], 2)],
        "n_reported": int(len(reported)),
        "n_ibef_forecasts": int(len(ibef)),
    }
