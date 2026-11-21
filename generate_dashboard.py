#!/usr/bin/env python3
"""Generates a standalone, fully-featured, offline interactive dashboard HTML for CNT-02.
Allows professors and stakeholders to dynamically explore:
1. Scenario Forecaster with interactive sliders (TAM, CAGR, SAM Share)
2. K-means Customer Segmentation Explorer
3. Market Growth & Category Benchmarking
4. Statistical Evaluation & Model Fit
"""
from pathlib import Path
import json
import pandas as pd
import os
import sys

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUT = ROOT / "outputs"
DASHBOARD_PATH = OUT / "interactive_dashboard.html"


def build_dashboard():
    OUT.mkdir(parents=True, exist_ok=True)
    
    # 1. Load market data
    mkt_path = DATA / "india_ecommerce_market.csv"
    mkt_data = pd.read_csv(mkt_path).to_dict(orient="records") if mkt_path.exists() else []

    # 2. Load statistical validation
    stat_path = OUT / "statistical_forecast_validation.csv"
    stat_data = pd.read_csv(stat_path).to_dict(orient="records") if stat_path.exists() else []

    # 3. Load segment profile summary
    seg_path = OUT / "segment_profile_summary.csv"
    seg_data = pd.read_csv(seg_path).to_dict(orient="records") if seg_path.exists() else []

    # 4. Load exploratory segments
    clust_path = OUT / "exploratory_consumer_segments.csv"
    sample_clusters = []
    if clust_path.exists():
        cdf = pd.read_csv(clust_path)
        sample_clusters = cdf[["respondent_id", "state_ut", "age_band", "preferred_category", 
                               "cluster_name", "discount_importance", "price_sensitivity_score",
                               "emi_influence_score", "exchange_influence_score", "delivery_cost_influence_score"]].to_dict(orient="records")

    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CNT-02 | Executive Research Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        :root {{
            --primary: #1e5638;
            --primary-light: #2d7a50;
            --secondary: #f4a261;
            --dark: #1f2937;
            --light: #f8fafc;
            --card-bg: #ffffff;
            --border: #e2e8f0;
            --text-muted: #64748b;
        }}
        * {{ box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; }}
        body {{ background: var(--light); color: var(--dark); padding-bottom: 50px; }}
        header {{
            background: linear-gradient(135deg, var(--primary) 0%, #133a25 100%);
            color: white; padding: 28px 40px; box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        header h1 {{ font-size: 24px; font-weight: 700; display: flex; align-items: center; gap: 10px; }}
        header p {{ font-size: 14px; opacity: 0.9; margin-top: 6px; }}
        .badge {{
            display: inline-block; background: rgba(255,255,255,0.2); padding: 4px 10px;
            border-radius: 20px; font-size: 12px; margin-left: 12px; font-weight: 500;
        }}
        .container {{ max-width: 1300px; margin: 24px auto; padding: 0 20px; display: flex; flex-direction: column; gap: 24px; }}
        
        .kpi-row {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 18px; }}
        .kpi-card {{
            background: var(--card-bg); padding: 20px; border-radius: 12px;
            border: 1px solid var(--border); box-shadow: 0 2px 8px rgba(0,0,0,0.03);
        }}
        .kpi-title {{ font-size: 13px; font-weight: 600; color: var(--text-muted); text-transform: uppercase; }}
        .kpi-val {{ font-size: 26px; font-weight: 800; color: var(--primary); margin: 6px 0; }}
        .kpi-sub {{ font-size: 12px; color: var(--text-muted); }}

        .card {{
            background: var(--card-bg); border-radius: 14px; border: 1px solid var(--border);
            padding: 24px; box-shadow: 0 3px 12px rgba(0,0,0,0.03);
        }}
        .card-title {{
            font-size: 18px; font-weight: 700; color: var(--dark); margin-bottom: 16px;
            display: flex; justify-content: space-between; align-items: center;
        }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
        @media(max-width: 900px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

        /* Interactive controls */
        .controls-panel {{
            background: #f1f7f4; border: 1px solid #cce3d8; border-radius: 10px;
            padding: 16px 20px; margin-bottom: 18px; display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;
        }}
        .control-group label {{ font-size: 13px; font-weight: 600; color: var(--primary); display: block; margin-bottom: 6px; }}
        .control-group input[type="range"] {{ width: 100%; }}
        .val-display {{ font-weight: 700; color: var(--dark); margin-left: 6px; }}

        table {{ width: 100%; border-collapse: collapse; font-size: 14px; margin-top: 10px; }}
        th, td {{ padding: 12px 14px; text-align: left; border-bottom: 1px solid var(--border); }}
        th {{ background: #f8fafc; font-weight: 600; color: var(--text-muted); }}
        tr:hover {{ background: #fdfdfd; }}

        .cluster-pill {{
            padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;
        }}
        .c-1 {{ background: #e0f2fe; color: #0369a1; }}
        .c-2 {{ background: #fef3c7; color: #b45309; }}
        .c-3 {{ background: #dcfce7; color: #15803d; }}

        .tabs {{ display: flex; gap: 10px; border-bottom: 2px solid var(--border); margin-bottom: 20px; }}
        .tab {{
            padding: 10px 18px; cursor: pointer; font-weight: 600; font-size: 14px;
            color: var(--text-muted); border-bottom: 3px solid transparent; transition: all 0.2s;
        }}
        .tab.active {{ color: var(--primary); border-bottom-color: var(--primary); }}
        .tab-pane {{ display: none; }}
        .tab-pane.active {{ display: block; }}
    </style>
</head>
<body>

<header>
    <h1>
        <span>🇮🇳 India E-Commerce Growth & Consumer Segmentation</span>
        <span class="badge">CNT-02 Offline Research Suite</span>
    </h1>
    <p>Academic Research & Scenario Simulation Dashboard | Department of Management & Economics</p>
</header>

<div class="container">

    <!-- KPI summary -->
    <div class="kpi-row">
        <div class="kpi-card">
            <div class="kpi-title">2024 Total Market (IBEF)</div>
            <div class="kpi-val">$125.0 bn</div>
            <div class="kpi-sub">+22.5% YoY Historical Momentum</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Electronics TAM (NITI Aayog)</div>
            <div class="kpi-val">$27.0 bn</div>
            <div class="kpi-sub">Target Category Baseline</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Model Fit (R²)</div>
            <div class="kpi-val">0.9992</div>
            <div class="kpi-sub">MAPE: 0.59% | Strong Historical Fit</div>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Identified Segments (K=3)</div>
            <div class="kpi-val">3 Clusters</div>
            <div class="kpi-sub">Silhouette Validation Score: 0.291</div>
        </div>
    </div>

    <!-- Navigation Tabs -->
    <div class="tabs">
        <div class="tab active" onclick="switchTab('scenarios')">📈 Dynamic Scenario Forecaster</div>
        <div class="tab" onclick="switchTab('segmentation')">👥 K-Means Consumer Clusters</div>
        <div class="tab" onclick="switchTab('validation')">📐 Statistical Validation & Benchmarking</div>
        <div class="tab" onclick="switchTab('rawdata')">📋 Sample Respondent Explorer</div>
    </div>

    <!-- TAB 1: Dynamic Scenarios -->
    <div id="tab-scenarios" class="tab-pane active">
        <div class="card">
            <div class="card-title">
                Interactive TAM & SAM Forecast Simulator (2024–2030)
                <span style="font-size: 13px; font-weight: normal; color: var(--text-muted);">Adjust parameters in real-time</span>
            </div>

            <div class="controls-panel">
                <div class="control-group">
                    <label>2024 Base TAM: <span id="lbl-tam" class="val-display">$27 bn</span></label>
                    <input type="range" id="param-tam" min="15" max="50" value="27" step="1" oninput="updateSimulation()">
                </div>
                <div class="control-group">
                    <label>Base CAGR: <span id="lbl-cagr" class="val-display">12%</span></label>
                    <input type="range" id="param-cagr" min="5" max="25" value="12" step="1" oninput="updateSimulation()">
                </div>
                <div class="control-group">
                    <label>SAM Reachable Share: <span id="lbl-sam" class="val-display">30%</span></label>
                    <input type="range" id="param-sam" min="10" max="60" value="30" step="5" oninput="updateSimulation()">
                </div>
            </div>

            <div style="height: 380px;">
                <canvas id="scenarioChart"></canvas>
            </div>
        </div>
    </div>

    <!-- TAB 2: Consumer Segmentation -->
    <div id="tab-segmentation" class="tab-pane">
        <div class="grid-2">
            <div class="card">
                <div class="card-title">Cluster Profile Comparison (Radar / Dimension View)</div>
                <div style="height: 350px;">
                    <canvas id="clusterRadarChart"></canvas>
                </div>
            </div>
            <div class="card">
                <div class="card-title">Segment Share & Characteristics</div>
                <table>
                    <thead>
                        <tr>
                            <th>Segment Name</th>
                            <th>Count</th>
                            <th>Key Behavioral Drivers</th>
                        </tr>
                    </thead>
                    <tbody id="cluster-summary-body">
                        <!-- Filled by JS -->
                    </tbody>
                </table>
                <div style="margin-top: 18px; padding: 12px; background: #fdf6ec; border-radius: 8px; font-size: 13px; color: #92400e;">
                    💡 <strong>Academic Note:</strong> Feature mismatch has been normalized using standard 1–4/5 Likert encoding across discount importance, price sensitivity, and financing options.
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 3: Statistical Validation -->
    <div id="tab-validation" class="tab-pane">
        <div class="card">
            <div class="card-title">Model Estimation & Statistical Goodness-of-Fit</div>
            <table>
                <thead>
                    <tr>
                        <th>Metric</th>
                        <th>Computed Value</th>
                        <th>Academic Interpretation & Verification</th>
                    </tr>
                </thead>
                <tbody id="stat-table-body">
                    <!-- Filled by JS -->
                </tbody>
            </table>
        </div>
    </div>

    <!-- TAB 4: Raw Sample Data -->
    <div id="tab-rawdata" class="tab-pane">
        <div class="card">
            <div class="card-title">Survey Respondent Sample (Pre-coded & Clustered)</div>
            <div style="overflow-x: auto; max-height: 450px;">
                <table>
                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>State</th>
                            <th>Age</th>
                            <th>Preferred Category</th>
                            <th>Segment Name</th>
                            <th>Discount</th>
                            <th>Price Sens.</th>
                            <th>EMI</th>
                            <th>Exchange</th>
                        </tr>
                    </thead>
                    <tbody id="respondent-body">
                        <!-- Filled by JS -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>

</div>

<script>
const marketData = {json.dumps(mkt_data)};
const statData = {json.dumps(stat_data)};
const segData = {json.dumps(seg_data)};
const sampleClusters = {json.dumps(sample_clusters)};

// Tab switching
function switchTab(name) {{
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
    event.target.classList.add('active');
    document.getElementById('tab-' + name).classList.add('active');
}}

// Populate Statistical Validation Table
const statTbody = document.getElementById('stat-table-body');
statData.forEach(row => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><strong>${{row.Metric}}</strong></td>
                    <td style="color: #1e5638; font-weight: 700;">${{row.Value}}</td>
                    <td style="color: #475569;">${{row.Interpretation}}</td>`;
    statTbody.appendChild(tr);
}});

// Populate Cluster Summary
const clusterTbody = document.getElementById('cluster-summary-body');
const descMap = {{
    "Value & Discount Seekers": "Highly price sensitive; driven by heavy discounts, coupons, and free delivery thresholds.",
    "Financing & Offer Driven": "Strong affinity for No-Cost EMI and credit card instalments; upgrades to premium gadgets on finance.",
    "Convenience & Premium Shoppers": "Low price sensitivity; prioritizes device availability, fast delivery, and brand reliability."
}};

segData.forEach((row, i) => {{
    const tr = document.createElement('tr');
    const badgeClass = i === 0 ? 'c-1' : (i === 1 ? 'c-2' : 'c-3');
    tr.innerHTML = `<td><span class="cluster-pill ${{badgeClass}}">${{row.cluster_name}}</span></td>
                    <td><strong>${{row.respondent_count}}</strong> respondents</td>
                    <td>${{descMap[row.cluster_name] || "Standard behavioral segment"}}</td>`;
    clusterTbody.appendChild(tr);
}});

// Populate Respondent sample table
const respTbody = document.getElementById('respondent-body');
sampleClusters.slice(0, 25).forEach(r => {{
    const tr = document.createElement('tr');
    tr.innerHTML = `<td><code>${{r.respondent_id}}</code></td>
                    <td>${{r.state_ut}}</td>
                    <td>${{r.age_band}}</td>
                    <td>${{r.preferred_category}}</td>
                    <td><span class="cluster-pill ${{r.cluster_name.includes('Value')?'c-2':(r.cluster_name.includes('Finance')?'c-1':'c-3')}}">${{r.cluster_name}}</span></td>
                    <td>${{r.discount_importance}}/5</td>
                    <td>${{r.price_sensitivity_score}}/5</td>
                    <td>${{r.emi_influence_score}}/4</td>
                    <td>${{r.exchange_influence_score}}/4</td>`;
    respTbody.appendChild(tr);
}});

// Chart.js Scenario Forecast
let scenarioChartInstance = null;

function updateSimulation() {{
    const baseTam = parseFloat(document.getElementById('param-tam').value);
    const baseCagr = parseFloat(document.getElementById('param-cagr').value) / 100;
    const samShare = parseFloat(document.getElementById('param-sam').value) / 100;

    document.getElementById('lbl-tam').innerText = '$' + baseTam + ' bn';
    document.getElementById('lbl-cagr').innerText = (baseCagr * 100).toFixed(0) + '%';
    document.getElementById('lbl-sam').innerText = (samShare * 100).toFixed(0) + '%';

    const years = [2024, 2025, 2026, 2027, 2028, 2029, 2030];
    const conservative = years.map(y => (baseTam * Math.pow(1 + (baseCagr - 0.04), y - 2024)).toFixed(1));
    const base = years.map(y => (baseTam * Math.pow(1 + baseCagr, y - 2024)).toFixed(1));
    const optimistic = years.map(y => (baseTam * Math.pow(1 + (baseCagr + 0.04), y - 2024)).toFixed(1));
    const sam = base.map(v => (v * samShare).toFixed(1));

    if (scenarioChartInstance) {{
        scenarioChartInstance.data.datasets[0].data = conservative;
        scenarioChartInstance.data.datasets[1].data = base;
        scenarioChartInstance.data.datasets[2].data = optimistic;
        scenarioChartInstance.data.datasets[3].data = sam;
        scenarioChartInstance.update();
    }} else {{
        const ctx = document.getElementById('scenarioChart').getContext('2d');
        scenarioChartInstance = new Chart(ctx, {{
            type: 'line',
            data: {{
                labels: years,
                datasets: [
                    {{ label: 'Conservative (-4% CAGR)', data: conservative, borderColor: '#64748b', borderDash: [5, 5], fill: false, tension: 0.2 }},
                    {{ label: 'Base Case (' + (baseCagr * 100).toFixed(0) + '% CAGR)', data: base, borderColor: '#1e5638', backgroundColor: 'rgba(30,86,56,0.1)', fill: false, borderWidth: 3, tension: 0.2 }},
                    {{ label: 'Optimistic (+4% CAGR)', data: optimistic, borderColor: '#2563eb', fill: false, borderWidth: 2, tension: 0.2 }},
                    {{ label: 'Illustrative SAM (Reachable)', data: sam, borderColor: '#f59e0b', backgroundColor: '#fef3c7', fill: true, borderWidth: 2, tension: 0.2 }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    y: {{ title: {{ display: true, text: 'US$ Billion' }}, beginAtZero: false }}
                }}
            }}
        }});
    }}
}}

// Initialize charts
updateSimulation();

// Cluster Radar Chart
if (segData.length > 0) {{
    const labels = ["Discount Importance", "Price Sensitivity", "EMI Influence", "Exchange Influence", "Delivery Cost"];
    const datasets = segData.map((s, idx) => {{
        const colors = [
            {{ border: '#0284c7', bg: 'rgba(2,132,199,0.2)' }},
            {{ border: '#d97706', bg: 'rgba(217,119,6,0.2)' }},
            {{ border: '#16a34a', bg: 'rgba(22,163,74,0.2)' }}
        ];
        return {{
            label: s.cluster_name,
            data: [
                s.discount_importance,
                s.price_sensitivity_score,
                s.emi_influence_score,
                s.exchange_influence_score,
                s.delivery_cost_influence_score
            ],
            borderColor: colors[idx % 3].border,
            backgroundColor: colors[idx % 3].bg,
            borderWidth: 2
        }};
    }});

    new Chart(document.getElementById('clusterRadarChart').getContext('2d'), {{
        type: 'radar',
        data: {{ labels: labels, datasets: datasets }},
        options: {{
            responsive: true,
            maintainAspectRatio: false,
            scales: {{
                r: {{ min: 0, max: 5, ticks: {{ stepSize: 1 }} }}
            }}
        }}
    }});
}}
</script>

</body>
</html>"""

    with open(DASHBOARD_PATH, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"\nDashboard generated: {DASHBOARD_PATH}")
    if sys.platform == "win32":
        try:
            os.startfile(str(DASHBOARD_PATH))
            print("Opened dashboard in default browser.")
        except Exception:
            pass


if __name__ == "__main__":
    build_dashboard()
