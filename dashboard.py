#!/usr/bin/env python3
"""Build a fully self-contained, offline interactive HTML dashboard.

Run via ``python run_project.py`` (or directly after the analysis has run).
The output, ``outputs/dashboard.html``, embeds Plotly.js and all result data —
the professor can open it in any modern browser with no server and no internet.
"""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.offline import get_plotlyjs
from plotly.subplots import make_subplots
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

import segmentation

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"

FEATURES = [
    "price_sensitivity", "discount_importance", "emi_influence",
    "exchange_influence", "delivery_cost_influence",
]
CLUSTER_COLOURS = ["#39856A", "#4C78A8", "#E39C37", "#8064A2", "#C44E52", "#55A868"]

LAYOUT = dict(
    template="plotly_white",
    font=dict(family="Segoe UI, Arial, sans-serif", size=12, color="#233a32"),
    paper_bgcolor="white",
    plot_bgcolor="white",
    margin=dict(l=55, r=25, t=45, b=50),
    hoverlabel=dict(bgcolor="white", font_size=12),
)
CONFIG = {
    "responsive": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["lasso2d", "select2d"],
}


def _read(name: str) -> list[dict]:
    path = OUT / name
    if not path.exists():
        return []
    return pd.read_csv(path).to_dict(orient="records")


def _apply(fig: go.Figure, height: int = 380, **kwargs) -> go.Figure:
    fig.update_layout(**LAYOUT, height=height, **kwargs)
    return fig


def _market_figure(market: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for status, colour, dash in [("Reported", "#39856A", "solid"),
                                 ("Forecast", "#8064A2", "dash")]:
        part = market[market.status.str.contains(status, case=False, na=False) &
                      market.market_scope.eq("India total e-commerce")]
        if part.empty:
            continue
        fig.add_trace(go.Scatter(
            x=part.year, y=part.market_value_usd_bn, mode="lines+markers",
            name=f"{status} (IBEF)",
            line=dict(color=colour, width=3, dash=dash), marker=dict(size=8),
            hovertemplate="%{x}: US$%{y:.0f}bn<extra>" + status + "</extra>",
        ))
    return _apply(fig, title="India total e-commerce market (US$ billion)",
                  xaxis_title="Year", yaxis_title="US$ billion",
                  legend=dict(orientation="h", y=-0.2))


def _category_figure(market: pd.DataFrame) -> go.Figure:
    part = market[market.market_scope.str.contains("electronics|smartphones", case=False,
                                                   na=False, regex=True)]
    labels = {
        "India online electronics and appliances": "Electronics & appliances",
        "India online smartphones (separate category)": "Smartphones",
    }
    part = part.copy()
    part["label"] = part.market_scope.map(labels).fillna(part.market_scope)
    part = part.sort_values("market_value_usd_bn")
    fig = go.Figure(go.Bar(
        x=part.market_value_usd_bn, y=part.label, orientation="h",
        marker_color="#39856A", text=part.market_value_usd_bn.map(lambda v: f"${v:.0f}bn"),
        textposition="outside", hovertemplate="%{y}: US$%{x:.0f}bn<extra></extra>",
    ))
    return _apply(fig, title="Online electronics categories, 2024 (NITI Aayog)",
                  xaxis_title="US$ billion", xaxis=dict(range=[0, part.market_value_usd_bn.max() * 1.25]))


def _tamsam_figure(tam: float, share: float) -> go.Figure:
    fig = go.Figure(go.Bar(
        x=["TAM", "Illustrative SAM"],
        y=[tam, tam * share],
        marker_color=["#4C78A8", "#E39C37"], text=[f"${tam:.1f}bn", f"${tam * share:.1f}bn"],
        textposition="outside", hovertemplate="%{x}: US$%{y:.1f}bn<extra></extra>",
    ))
    return _apply(fig, title=f"2024 market sizing (SAM = {share:.0%} of TAM)",
                  yaxis_title="US$ billion", yaxis=dict(range=[0, tam * 1.3]))


def _scenario_figure(tam: float, share: float) -> go.Figure:
    years = np.arange(2024, 2036)
    fig = go.Figure()
    for label, rate, colour in [("Conservative", 0.08, "#4C78A8"),
                                ("Base", 0.12, "#39856A"),
                                ("Optimistic", 0.16, "#E39C37")]:
        fig.add_trace(go.Scatter(
            x=years, y=tam * (1 + rate) ** (years - 2024), mode="lines+markers",
            name=f"{label} ({rate:.0%})", line=dict(color=colour, width=2.5),
            hovertemplate="%{x}: US$%{y:.1f}bn<extra>" + label + "</extra>",
        ))
    return _apply(fig, title="Electronics TAM scenarios, 2024-2035",
                  xaxis_title="Year", yaxis_title="US$ billion",
                  legend=dict(orientation="h", y=-0.2))


def _sensitivity_figure(rows: list[dict]) -> go.Figure:
    if not rows:
        return _apply(go.Figure(), title="CAGR sensitivity")
    frame = pd.DataFrame(rows)
    colours = np.where(frame.cagr_pct.eq(12), "#39856A", "#B7CDC4")
    fig = go.Figure(go.Bar(
        x=frame.cagr_pct.astype(str) + "%", y=frame.tam_2030_usd_bn,
        marker_color=colours,
        text=frame.tam_2030_usd_bn.map(lambda v: f"${v:.1f}bn"), textposition="outside",
        hovertemplate="%{x}: US$%{y:.1f}bn<extra></extra>",
    ))
    return _apply(fig, title="2030 TAM sensitivity to the CAGR assumption",
                  xaxis_title="Assumed CAGR", yaxis_title="US$ billion",
                  yaxis=dict(range=[0, frame.tam_2030_usd_bn.max() * 1.2]))


def _cluster_figure() -> go.Figure:
    fig = go.Figure()
    path = OUT / "exploratory_consumer_segments.csv"
    if not path.exists():
        return _apply(fig, title="Consumer segments (no survey data)")
    frame = pd.read_csv(path)
    if not all(c in frame for c in FEATURES):
        return _apply(fig, title="Consumer segments (insufficient features)")
    # Reuse the exact questionnaire encoding from the analysis pipeline.
    _, encoded, _ = segmentation.encode_features(frame)
    X = StandardScaler().fit_transform(encoded.to_numpy(dtype=float))
    coords = PCA(n_components=2, random_state=42).fit_transform(X)
    for cluster in sorted(frame.cluster.unique()):
        mask = frame.cluster.eq(cluster).to_numpy()
        colour = CLUSTER_COLOURS[(int(cluster) - 1) % len(CLUSTER_COLOURS)]
        label = frame.loc[mask, "segment_label"].iloc[0] if "segment_label" in frame else f"Segment {cluster}"
        fig.add_trace(go.Scatter(
            x=coords[mask, 0], y=coords[mask, 1], mode="markers",
            marker=dict(size=9, color=colour, opacity=.85, line=dict(width=.5, color="white")),
            name=f"Segment {cluster}", text=label,
            hovertemplate="PC1 %{x:.2f}, PC2 %{y:.2f}<extra>%{text}</extra>",
        ))
    return _apply(fig, title="Respondents in 2-D feature space (PCA)",
                  xaxis_title="Principal component 1", yaxis_title="Principal component 2",
                  legend=dict(orientation="h", y=-0.2))


def _profile_figure(rows: list[dict]) -> go.Figure:
    if not rows:
        return _apply(go.Figure(), title="Cluster profiles")
    frame = pd.DataFrame(rows)
    columns = [f + "_mean" for f in FEATURES if f + "_mean" in frame]
    labels = ["Price sens.", "Discount", "EMI", "Exchange", "Delivery cost"][:len(columns)]
    z = np.array([
        [(row[col] - frame[col].mean()) / (frame[col].std(ddof=0) or 1) for col in columns]
        for _, row in frame.iterrows()
    ])
    fig = go.Figure(go.Heatmap(
        z=z, x=labels, y=[f"C{int(r.cluster)}" for r in frame.itertuples()],
        colorscale="RdYlGn", zmid=0, zmin=-1.7, zmax=1.7,
        colorbar=dict(title="SD vs mean", thickness=12),
        text=np.round(z, 2), texttemplate="%{text}",
        hovertemplate="%{y} / %{x}: %{z:+.2f} SD<extra></extra>",
    ))
    return _apply(fig, title="Cluster influence profiles (standardised means)", height=340)


def _k_figure(rows: list[dict], best_k: int) -> go.Figure:
    if not rows:
        return _apply(go.Figure(), title="Selecting the number of clusters")
    frame = pd.DataFrame(rows)
    fig = make_subplots(rows=1, cols=2, subplot_titles=(
        "Silhouette (higher is better)", "Inertia / elbow (lower is better)"))
    fig.add_trace(go.Scatter(x=frame.k, y=frame.silhouette, mode="lines+markers",
                             name="Silhouette", line=dict(color="#39856A", width=3),
                             marker=dict(size=9)), row=1, col=1)
    fig.add_vline(x=best_k, line=dict(color="#E39C37", dash="dash"), row=1, col=1)
    fig.add_trace(go.Scatter(x=frame.k, y=frame.inertia, mode="lines+markers",
                             name="Inertia", line=dict(color="#4C78A8", width=3),
                             marker=dict(size=9)), row=1, col=2)
    fig.update_xaxes(title_text="k", row=1, col=1)
    fig.update_xaxes(title_text="k", row=1, col=2)
    fig.update_yaxes(title_text="Score", range=[0, 1], row=1, col=1)
    return _apply(fig, title=f"Cluster validation — selected k = {best_k}", height=360,
                  showlegend=False)


def _backtest_figure(backtest: list[dict], market: pd.DataFrame) -> go.Figure:
    reported = market[market.status.str.contains("Reported", case=False, na=False) &
                      market.market_scope.eq("India total e-commerce")]
    fig = go.Figure(go.Scatter(x=reported.year, y=reported.market_value_usd_bn,
                               mode="lines+markers", name="Reported",
                               line=dict(color="#233a32", width=3)))
    colours = {"CAGR (log-linear)": "#39856A", "Linear trend": "#4C78A8",
               "Holt exponential smoothing": "#E39C37", "Naive (last value)": "#8064A2"}
    for row in backtest:
        fig.add_trace(go.Scatter(
            x=[row["year"]], y=[row["predicted_usd_bn"]], mode="markers",
            marker=dict(symbol="x", size=12, line=dict(width=2.5,
                        color=colours.get(row["model"], "#888"))),
            name=row["model"], legendgroup=row["model"],
            showlegend=row["year"] == backtest[0]["year"],
            hovertemplate=f"{row['model']} / {row['year']}: US$%{{y:.1f}}bn"
                          f" (actual US${row['actual_usd_bn']:.0f}bn)<extra></extra>",
        ))
    return _apply(fig, title="Rolling-origin backtest — x = forecast, line = reported",
                  xaxis_title="Year", yaxis_title="US$ billion",
                  legend=dict(orientation="h", y=-0.2))


def _benchmark_figure(intervals: list[dict], growth: list[dict]) -> go.Figure:
    fig = go.Figure()
    if intervals:
        frame = pd.DataFrame(intervals)
        fig.add_trace(go.Scatter(
            x=list(frame.year) + list(frame.year[::-1]),
            y=list(frame.pi95_high_usd_bn) + list(frame.pi95_low_usd_bn[::-1]),
            fill="toself", fillcolor="rgba(57,133,106,0.15)", line=dict(width=0),
            name="95% prediction interval", hoverinfo="skip",
        ))
        fig.add_trace(go.Scatter(x=frame.year, y=frame.cagr_point_estimate_usd_bn,
                                 mode="lines", name="Fitted CAGR trend",
                                 line=dict(color="#39856A", dash="dash", width=2)))
        published = frame.dropna(subset=["ibef_published_usd_bn"])
        if not published.empty:
            fig.add_trace(go.Scatter(x=published.year, y=published.ibef_published_usd_bn,
                                     mode="lines+markers", name="IBEF published forecast",
                                     line=dict(color="#233a32", width=3),
                                     marker=dict(size=8)))
    return _apply(fig, title="Published IBEF forecast vs fitted trend (benchmarks, not outcomes)",
                  xaxis_title="Year", yaxis_title="US$ billion",
                  legend=dict(orientation="h", y=-0.2))


def build(market: pd.DataFrame, scenarios: pd.DataFrame, tam: float, share: float,
          segmentation_summary: dict | None = None,
          forecast_summary: dict | None = None,
          using_sample: bool = False) -> Path:
    """Generate outputs/dashboard.html and return its path."""
    segmentation_summary = segmentation_summary or {}
    forecast_summary = forecast_summary or {}

    figs = {
        "market": _market_figure(market),
        "category": _category_figure(market),
        "tamsam": _tamsam_figure(tam, share),
        "scenario": _scenario_figure(tam, share),
        "sensitivity": _sensitivity_figure(forecast_summary.get("cagr_sensitivity", [])),
        "clusters": _cluster_figure(),
        "profile": _profile_figure(segmentation_summary.get("profiles", [])),
        "k": _k_figure(segmentation_summary.get("k_selection", []),
                       segmentation_summary.get("best_k", 3)),
        "backtest": _backtest_figure(forecast_summary.get("backtest", []), market),
        "benchmark": _benchmark_figure(forecast_summary.get("prediction_intervals", []),
                                       forecast_summary.get("growth_rate_benchmarks", [])),
    }
    fig_json = {name: json.loads(fig.to_json()) for name, fig in figs.items()}

    reported_total = market[
        market.status.str.contains("Reported", case=False, na=False)
        & market.market_scope.eq("India total e-commerce")
    ]
    recent = reported_total.loc[reported_total.year.eq(2024), "market_value_usd_bn"]
    market_2024 = float(recent.iloc[0]) if not recent.empty else 0.0

    kpis = {
        "market_2024": market_2024,
        "electronics_tam": tam,
        "base_2030": round(tam * 1.12 ** 6, 1),
        "sample_n": segmentation_summary.get("encoding", {}).get("rows_used", 0),
        "best_k": segmentation_summary.get("best_k", "n/a"),
        "silhouette": segmentation_summary.get("silhouette", "n/a"),
        "fitted_cagr": forecast_summary.get("fitted_cagr_pct", "n/a"),
        "fitted_cagr_ci": forecast_summary.get("fitted_cagr_ci", []),
        "model_comparison": forecast_summary.get("model_comparison", []),
    }

    payload = {
        "figs": fig_json,
        "market": market.to_dict(orient="records"),
        "scenarios": scenarios.to_dict(orient="records"),
        "tam": tam,
        "sam_share": share,
        "ibef": forecast_summary.get("ibef_forecasts", []),
        "profiles": segmentation_summary.get("profiles", []),
        "validation": segmentation_summary,
        "growth": forecast_summary.get("growth_rate_benchmarks", []),
        "model_comparison": forecast_summary.get("model_comparison", []),
        "cagr_sensitivity": forecast_summary.get("cagr_sensitivity", []),
        "backtest": forecast_summary.get("backtest", []),
        "kpis": kpis,
        "using_sample": using_sample,
        "generated": date.today().strftime("%d %B %Y"),
    }
    data_json = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")

    html = _HTML_TEMPLATE.replace("__PLOTLY_JS__", get_plotlyjs()) \
                         .replace("__PLOTLY_CONFIG__", json.dumps(CONFIG)) \
                         .replace("__GENERATED__", payload["generated"]) \
                         .replace("__DATA_JSON__", data_json)
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / "dashboard.html"
    path.write_text(html, encoding="utf-8")
    return path


_HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CNT-02 | Interactive Results Dashboard</title>
<script>__PLOTLY_JS__</script>
<style>
:root{--ink:#233a32;--muted:#60776e;--green:#39856a;--green-dark:#1d4f3c;
      --bg:#f3f6f4;--card:#ffffff;--line:#dce7e1;--amber:#e39c37}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
     font-family:"Segoe UI",Arial,sans-serif;font-size:14px;line-height:1.5}
header{background:linear-gradient(120deg,#123a2d,#1d5c46);color:#fff;padding:26px 34px 22px;
       box-shadow:0 2px 12px rgba(0,0,0,.12)}
header h1{margin:0;font-size:26px;letter-spacing:.2px}
header p{margin:6px 0 0;color:#cfe4da;font-size:13.5px}
.badges{margin-top:12px;display:flex;gap:8px;flex-wrap:wrap}
.badge{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.28);
       border-radius:99px;padding:3px 11px;font-size:11.5px;color:#eaf5ef}
.badge.warn{background:rgba(227,156,55,.22);border-color:#e3a95f}
main{max-width:1500px;margin:0 auto;padding:22px 26px 60px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(168px,1fr));gap:14px;margin-bottom:20px}
.kpi{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:15px 17px;
     box-shadow:0 2px 8px rgba(20,60,45,.05)}
.kpi .label{font-size:11px;text-transform:uppercase;letter-spacing:.7px;color:var(--muted)}
.kpi .value{font-size:26px;font-weight:700;color:var(--green-dark);margin-top:3px}
.kpi .sub{font-size:11.5px;color:var(--muted)}
nav.tabs{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px;border-bottom:1px solid var(--line);
         padding-bottom:8px}
nav.tabs button{border:1px solid transparent;background:transparent;color:var(--muted);
     padding:9px 16px;border-radius:9px;cursor:pointer;font-size:13.5px;font-weight:600}
nav.tabs button:hover{background:#e8f1ec;color:var(--green-dark)}
nav.tabs button.active{background:var(--green);color:#fff;box-shadow:0 3px 8px rgba(57,133,106,.25)}
.panel{display:none;animation:fade .25s ease}
.panel.active{display:block}
@keyframes fade{from{opacity:0;transform:translateY(4px)}to{opacity:1;transform:none}}
.grid{display:grid;gap:16px}
.grid.two{grid-template-columns:repeat(auto-fit,minmax(430px,1fr))}
.card{background:var(--card);border:1px solid var(--line);border-radius:13px;padding:16px 18px 12px;
      box-shadow:0 2px 10px rgba(20,60,45,.05);margin-bottom:16px}
.card h3{margin:0 0 2px;font-size:16px;color:var(--green-dark)}
.card p.note{margin:2px 0 10px;color:var(--muted);font-size:12.5px}
.controls{display:flex;gap:20px;flex-wrap:wrap;align-items:center;background:#f7faf8;
          border:1px solid var(--line);border-radius:10px;padding:12px 16px;margin-bottom:14px}
.control{display:flex;flex-direction:column;min-width:210px;flex:1}
.control label{font-size:12px;color:var(--muted);font-weight:600}
.control output{font-weight:700;color:var(--green-dark)}
input[type=range]{width:100%;accent-color:var(--green)}
table{width:100%;border-collapse:collapse;font-size:12.5px}
th{text-align:left;background:#eef5f1;color:var(--green-dark);font-size:11.5px;
   text-transform:uppercase;letter-spacing:.4px;padding:8px 10px;border-bottom:2px solid var(--line)}
td{padding:7px 10px;border-bottom:1px solid #edf2ef}
tr:hover td{background:#f8fbf9}
.wrap{overflow-x:auto}
.segment-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px;margin:8px 0 14px}
.segment-card{border-left:4px solid var(--green);background:#f7faf8;border-radius:8px;padding:11px 14px}
.segment-card b{color:var(--green-dark)}
.callout{background:#fff8ec;border:1px solid #f0d9ae;border-left:4px solid var(--amber);
         border-radius:9px;padding:12px 15px;font-size:13px;color:#6b5227;margin:12px 0}
.methods{display:grid;grid-template-columns:repeat(auto-fit,minmax(420px,1fr));gap:16px}
button.download{background:#fff;border:1px solid var(--green);color:var(--green-dark);
   border-radius:8px;padding:7px 12px;cursor:pointer;font-size:12px;font-weight:600;margin:3px 5px 3px 0}
button.download:hover{background:#e8f1ec}
footer{text-align:center;color:var(--muted);font-size:12px;padding:20px}
code{background:#eef3f0;padding:1px 5px;border-radius:4px;font-size:12px}
@media(max-width:700px){header{padding:20px}main{padding:16px}.grid.two{grid-template-columns:1fr}}
</style>
</head>
<body>
<header>
  <h1>CNT-02 &middot; India E-Commerce Market &amp; Consumer Segments</h1>
  <p>Interactive results explorer &mdash; IBEF / NITI Aayog benchmarks, consumer survey segmentation and model validation</p>
  <div class="badges">
    <span class="badge">Fully offline &mdash; no internet required</span>
    <span class="badge">Generated __GENERATED__</span>
    <span class="badge" id="data-badge"></span>
  </div>
</header>
<main>
  <section class="kpis">
    <div class="kpi"><div class="label">Total market 2024</div><div class="value" id="kpi-market"></div><div class="sub">IBEF reported</div></div>
    <div class="kpi"><div class="label">Electronics TAM 2024</div><div class="value" id="kpi-tam"></div><div class="sub">NITI Aayog estimate</div></div>
    <div class="kpi"><div class="label">Base 2030 projection</div><div class="value" id="kpi-base"></div><div class="sub">12% CAGR scenario</div></div>
    <div class="kpi"><div class="label">Survey sample</div><div class="value" id="kpi-n"></div><div class="sub">usable responses</div></div>
    <div class="kpi"><div class="label">Clusters (k)</div><div class="value" id="kpi-k"></div><div class="sub" id="kpi-sil"></div></div>
    <div class="kpi"><div class="label">Fitted CAGR 21&ndash;24</div><div class="value" id="kpi-cagr"></div><div class="sub" id="kpi-ci"></div></div>
  </section>

  <nav class="tabs">
    <button class="active" data-tab="market">Market overview</button>
    <button data-tab="scenarios">Scenario explorer</button>
    <button data-tab="segments">Consumer segments</button>
    <button data-tab="validation">Statistical validation</button>
    <button data-tab="methods">Data &amp; methods</button>
  </nav>

  <section class="panel active" id="tab-market">
    <div class="grid two">
      <div class="card"><h3>Market trajectory</h3><p class="note">Reported values and published forecasts shown as separate series.</p><div id="plot-market"></div></div>
      <div class="card"><h3>Category benchmark</h3><p class="note">Two separately classified online electronics categories (2024).</p><div id="plot-category"></div></div>
    </div>
    <div class="card"><h3>Market sizing</h3><p class="note">SAM is an illustrative assumption, not an observed figure.</p><div id="plot-tamsam"></div></div>
  </section>

  <section class="panel" id="tab-scenarios">
    <div class="card">
      <h3>Build your own projection</h3>
      <p class="note">Move the sliders to test how the 2030 TAM / SAM responds to the assumptions. The three published scenarios remain for comparison.</p>
      <div class="controls">
        <div class="control"><label>Assumed CAGR: <output id="out-rate">12%</output></label><input id="rate" type="range" min="4" max="28" step="1" value="12"></div>
        <div class="control"><label>Reachable SAM share: <output id="out-share">30%</output></label><input id="share" type="range" min="5" max="60" step="1" value="30"></div>
        <div class="control"><label>2024 TAM (US$bn): <output id="out-tam"></output></label><input id="tam" type="range" min="10" max="60" step="1" value="27"></div>
      </div>
      <div id="plot-scenario-custom"></div>
      <div class="wrap"><table id="scenario-table"></table></div>
    </div>
    <div class="card"><h3>Sensitivity to the growth assumption</h3><p class="note">Computed with the project's fixed 30% SAM share.</p><div id="plot-sensitivity"></div></div>
  </section>

  <section class="panel" id="tab-segments">
    <div class="grid two">
      <div class="card"><h3>Segment structure</h3><p class="note">Each point is one respondent; X marks a segment centre. Axes are principal components of the five encoded influence scores.</p><div id="plot-clusters"></div></div>
      <div class="card"><h3>Segment profiles</h3><p class="note">Red = below the survey mean, green = above it (standard deviations).</p><div id="plot-profile"></div></div>
    </div>
    <div class="card"><h3>Segment summaries</h3><div class="segment-grid" id="segment-cards"></div>
      <div class="wrap"><table id="cluster-table"></table></div>
      <div class="callout">Segment names are interpretive labels derived from the highest standardised feature means. K-means is exploratory; confirm with a larger, representative sample before acting on these labels.</div>
    </div>
  </section>

  <section class="panel" id="tab-validation">
    <div class="grid two">
      <div class="card"><h3>Choosing k</h3><p class="note">Silhouette and inertia are computed for k = 2&ndash;6. The highest silhouette is selected automatically.</p><div id="plot-k"></div></div>
      <div class="card"><h3>Cluster reliability</h3><p class="note">Adjusted Rand Index measures agreement with the full-data solution: 1 = perfect, 0 = chance.</p><div class="wrap"><table id="cluster-validation-table"></table></div><div class="wrap"><table id="feature-significance-table"></table></div><div id="permutation-note" class="callout"></div></div>
    </div>
    <div class="card"><h3>Forecast backtest</h3><p class="note">Each forecast uses only earlier reported years. With four reported points, n = 2 per model: diagnostic only.</p><div id="plot-backtest"></div></div>
    <div class="grid two">
      <div class="card"><h3>Model scorecard</h3><div class="wrap"><table id="forecast-table"></table></div>
        <div class="callout">The model with the best two-year backtest is not necessarily the best at a 5-10 year horizon: a curved fit to four points tracks recent growth well but over-extrapolates. Use the scenario band, not a single line, for decisions.</div>
      </div>
      <div class="card"><h3>Published forecast benchmark</h3><p class="note">IBEF values are projections, not outcomes. The shaded band is a 95% prediction interval from the fitted trend.</p><div id="plot-benchmark"></div></div>
    </div>
    <div class="card"><h3>Implied growth rates</h3><div class="wrap"><table id="growth-table"></table></div></div>
  </section>

  <section class="panel" id="tab-methods">
    <div class="methods">
      <div class="card"><h3>Survey response data</h3><p class="note" id="data-provenance"></p>
        <div class="callout" id="mismatch-note"></div>
        <div class="wrap"><table id="encoding-table"></table></div>
        <div style="margin-top:12px">
          <button class="download" id="dl-segments">Download segment assignments (CSV)</button>
          <button class="download" id="dl-profiles">Download cluster profiles (CSV)</button>
          <button class="download" id="dl-backtest">Download forecast backtest (CSV)</button>
        </div>
      </div>
      <div class="card"><h3>How to read the validation</h3>
        <ul>
          <li><b>Silhouette</b> (0 to 1) measures how tightly respondents fit their cluster versus the next nearest one.</li>
          <li><b>Adjusted Rand Index</b> compares partitions across random seeds and 80% bootstrap resamples.</li>
          <li><b>Permutation test</b> shuffles each feature independently; a small p-value means the observed structure is unlikely to be random noise.</li>
          <li><b>Backtest MAPE</b> is the mean absolute percentage error of one-step-ahead forecasts on reported years.</li>
        </ul>
        <div class="callout"><b>Interpret with care.</b> The market series has only four reported observations, so fitted confidence intervals are wide and backtests contain two predictions per model. The 8% / 12% / 16% scenario rates are assumptions, not estimates. The consumer sample is a convenience sample and is not nationally representative.</div>
      </div>
    </div>
  </section>
</main>
<footer>CNT-02 &middot; Fully offline academic analysis &middot; Generate with <code>python run_project.py</code></footer>
<script>
const DATA = __DATA_JSON__;
const CONFIG = __PLOTLY_CONFIG__;
const $ = (id) => document.getElementById(id);
const fmt = (v, d = 1) => (v === null || v === undefined || isNaN(v) ? "n/a" : Number(v).toFixed(d));

document.querySelectorAll("nav.tabs button").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll("nav.tabs button").forEach(b => b.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
    btn.classList.add("active");
    $("tab-" + btn.dataset.tab).classList.add("active");
    window.dispatchEvent(new Event("resize"));
  });
});

function draw(id, fig) {
  if (!fig || !fig.data || !fig.data.length) { $(id).innerHTML = "<p class='note'>No data available.</p>"; return; }
  Plotly.newPlot(id, fig.data, Object.assign({}, fig.layout, {autosize: true}), CONFIG);
}
Object.entries(DATA.figs).forEach(([name, fig]) => {
  const target = name === "scenario" ? "plot-scenario-custom" : "plot-" + name;
  if ($(target)) draw(target, fig);
});

const k = DATA.kpis;
$("kpi-market").textContent = "$" + fmt(k.market_2024, 0) + "bn";
$("kpi-tam").textContent = "$" + fmt(k.electronics_tam, 1) + "bn";
$("kpi-base").textContent = "$" + fmt(k.base_2030, 1) + "bn";
$("kpi-n").textContent = k.sample_n || "0";
$("kpi-k").textContent = k.best_k;
$("kpi-sil").textContent = "silhouette " + fmt(k.silhouette, 3);
$("kpi-cagr").textContent = fmt(k.fitted_cagr, 1) + "%";
$("kpi-ci").textContent = k.fitted_cagr_ci.length ? "95% CI " + fmt(k.fitted_cagr_ci[0], 1) + "–" + fmt(k.fitted_cagr_ci[1], 1) + "%" : "";
$("data-badge").textContent = DATA.using_sample ? "Illustrative sample survey" : "Local survey responses";
$("data-provenance").textContent = DATA.using_sample
  ? "Demonstration uses 60 ILLUSTRATIVE SYNTHETIC responses (scripts/make_sample_survey.py). Replace data/survey_responses.csv with real consented data to rerun."
  : "Analysis used data/survey_responses.csv (local, consented responses).";
$("mismatch-note").innerHTML = "<b>K-means feature mismatch fixed.</b> The old pipeline looked for non-existent <code>*_influence_score</code> columns and coerced text answers to NaN, leaving 0 usable rows. The corrected pipeline reads the real ordinal columns and uses <b>" +
  (k.sample_n || 0) + "</b> valid responses.";

function table(id, headers, rows) {
  const head = "<thead><tr>" + headers.map(h => "<th>" + h + "</th>").join("") + "</tr></thead>";
  const body = "<tbody>" + rows.map(r => "<tr>" + r.map(c => "<td>" + c + "</td>").join("") + "</tr>").join("") + "</tbody>";
  $(id).innerHTML = "<table>" + head + body + "</table>";
}

// --- scenario explorer -------------------------------------------------
function projectionTraces(rate, share, tam) {
  const years = [];
  for (let y = 2024; y <= 2035; y++) years.push(y);
  const lines = [["Your projection (" + rate + "% CAGR)", rate, "#c0392b"],
                 ["Base (12%)", 12, "#39856a"],
                 ["Conservative (8%)", 8, "#4c78a8"],
                 ["Optimistic (16%)", 16, "#e39c37"]];
  const traces = lines.map(([name, r, colour]) => ({
    x: years, y: years.map(y => tam * Math.pow(1 + r / 100, y - 2024)),
    type: "scatter", mode: "lines+markers", name,
    line: {color: colour, width: name.startsWith("Your") ? 4 : 2,
           dash: name.startsWith("Your") ? "solid" : "dot"}
  }));
  traces.push({x: years, y: years.map(y => tam * Math.pow(1 + rate / 100, y - 2024) * share),
    type: "scatter", mode: "lines", name: "Your SAM (" + Math.round(share * 100) + "%)",
    line: {color: "#7f8c8d", width: 2, dash: "dash"}});
  if (DATA.ibef && DATA.ibef.length) {
    traces.push({x: DATA.ibef.map(r => r.year), y: DATA.ibef.map(r => r.value),
      type: "scatter", mode: "markers+lines", name: "IBEF published forecast",
      line: {color: "#222", width: 2}, marker: {size: 7}});
  }
  return traces;
}
function updateScenario() {
  const rate = +$("rate").value, share = +$("share").value / 100, tam = +$("tam").value;
  $("out-rate").textContent = rate + "%";
  $("out-share").textContent = Math.round(share * 100) + "%";
  $("out-tam").textContent = "$" + tam + "bn";
  Plotly.react("plot-scenario-custom", projectionTraces(rate, share, tam),
    Object.assign({}, DATA.figs.scenario.layout, {height: 420}), CONFIG);
  const rows = [2024, 2027, 2030, 2035].map(y => {
    const value = tam * Math.pow(1 + rate / 100, y - 2024);
    return [y, "$" + value.toFixed(1) + "bn", "$" + (value * share).toFixed(1) + "bn"];
  });
  table("scenario-table", ["Year", "Your TAM", "Your SAM"], rows);
}
["rate", "share", "tam"].forEach(id => $(id).addEventListener("input", updateScenario));
updateScenario();

// --- segments ----------------------------------------------------------
const profiles = DATA.profiles || [];
if (profiles.length) {
  $("segment-cards").innerHTML = profiles.map((p, i) => {
    const colour = ["#39856a", "#4c78a8", "#e39c37", "#8064a2", "#c44e52"][i % 5];
    return "<div class='segment-card' style='border-left-color:" + colour + "'><b>" + p.segment_label +
      "</b><br>" + fmt(p.n, 0) + " respondents (" + fmt(p.share_pct, 1) + "%)<br>" +
      "Typical spend: " + p.typical_spend_band + "</div>";
  }).join("");
  table("cluster-table",
    ["Cluster", "n", "Price", "Discount", "EMI", "Exchange", "Delivery", "Typical spend"],
    profiles.map(p => [p.cluster, p.n, p.price_sensitivity_mean, p.discount_importance_mean,
      p.emi_influence_mean, p.exchange_influence_mean, p.delivery_cost_influence_mean,
      p.typical_spend_band]));
}

// --- validation --------------------------------------------------------
const val = (DATA.validation && DATA.validation.stability) || {};
const perm = (DATA.validation && DATA.validation.permutation) || {};
const vRows = [
  ["Selected k", DATA.validation.best_k || "n/a"],
  ["Silhouette score", fmt(DATA.validation.silhouette, 3)],
  ["Seed stability (mean ARI)", fmt(val.seed_ari_mean, 3)],
  ["Bootstrap stability (mean ARI)", fmt(val.bootstrap_ari_mean, 3)],
  ["Bootstrap 5th percentile ARI", fmt(val.bootstrap_ari_p05, 3)],
  ["Permutation p-value", fmt(perm.p_value, 4)],
];
table("cluster-validation-table", ["Metric", "Value"], vRows);

const sig = DATA.validation.feature_significance || [];
if (sig.length) {
  const pText = p => (p < 0.001 ? "<0.001" : fmt(p, 3));
  table("feature-significance-table", ["Feature", "Kruskal H", "p-value", "Effect size (eta^2)"],
    sig.map(s => [s.feature, fmt(s.kruskal_H, 2), pText(s.p_value), fmt(s.eta_squared, 3)]));
}
$("permutation-note").innerHTML = "<b>Permutation test:</b> observed silhouette " +
  fmt(perm.observed_silhouette, 3) + " vs permuted mean " + fmt(perm.permuted_silhouette_mean, 3) +
  " over " + (perm.n_permutations || 0) + " shuffles (p = " + fmt(perm.p_value, 4) + "). " +
  (perm.p_value !== undefined && perm.p_value < 0.05
    ? "Cluster structure is unlikely under random feature shuffling."
    : "Evidence is suggestive only; collect more responses.");

const models = DATA.model_comparison || [];
if (models.length) table("forecast-table",
  ["Model", "Backtest n", "MAE", "MAPE", "IBEF benchmark MAPE", "in-sample R²"],
  models.map(m => [m.model, m.backtest_n, "$" + fmt(m.backtest_MAE_usd_bn, 2) + "bn",
    fmt(m.backtest_MAPE_pct, 1) + "%", fmt(m.ibef_benchmark_MAPE_pct, 1) + "%",
    fmt(m.in_sample_R2, 3)]));

if ((DATA.growth || []).length) table("growth-table",
  ["Benchmark", "Period", "CAGR", "95% CI", "Status"],
  DATA.growth.map(g => [g.benchmark, g.period, fmt(g.cagr_pct, 1) + "%",
    (g.ci_low_pct === null || g.ci_low_pct === undefined || isNaN(g.ci_low_pct))
      ? "—" : fmt(g.ci_low_pct, 1) + "% to " + fmt(g.ci_high_pct, 1) + "%", g.note]));

table("encoding-table", ["Feature", "Question", "Encoded scale", "Missing answers"],
  [["price_sensitivity", "Q9 price sensitivity", "1–5", "—"],
   ["discount_importance", "Q10 discount importance", "1–5", "—"],
   ["emi_influence", "Q11 no-cost EMI", "1–4; Unsure = missing", "—"],
   ["exchange_influence", "Q12 exchange offer", "1–4; N/A = missing", "—"],
   ["delivery_cost_influence", "Q13 delivery cost", "1–4", "—"]]);

function downloadCSV(id, rows) {
  if (!rows || !rows.length) return;
  const keys = Object.keys(rows[0]);
  const escape = v => '"' + String(v === null || v === undefined ? "" : v).replace(/"/g, '""') + '"';
  const csv = [keys.map(escape).join(",")].concat(rows.map(r => keys.map(k2 => escape(r[k2])).join(","))).join("\n");
  const url = URL.createObjectURL(new Blob([csv], {type: "text/csv;charset=utf-8"}));
  const a = document.createElement("a");
  a.href = url; a.download = id + ".csv"; a.click();
  URL.revokeObjectURL(url);
}
$("dl-segments").addEventListener("click", () => downloadCSV("consumer_segment_assignments",
  (DATA.validation.assignments || [])));
$("dl-profiles").addEventListener("click", () => downloadCSV("cluster_profiles", profiles));
$("dl-backtest").addEventListener("click", () => downloadCSV("forecast_backtest",
  DATA.backtest || []));
</script>
</body>
</html>
"""
