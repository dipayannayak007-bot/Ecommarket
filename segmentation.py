#!/usr/bin/env python3
"""Validated K-means consumer segmentation for the CNT-02 survey.

WHAT WAS BROKEN
---------------
The original pipeline in ``run_project.py`` looked for numeric columns called
``emi_influence_score``, ``exchange_influence_score`` and
``delivery_cost_influence_score``. The real survey schema
(``data/survey_template.csv``) has no such columns: it stores ordinal TEXT
answers (``Not at all``, ``A little``, ``Somewhat``, ``A lot``, ...) in
``emi_influence``, ``exchange_influence`` and ``delivery_cost_influence``.
``pd.to_numeric`` therefore turned every value into NaN and no clustering ever
ran. This module maps the questionnaire's actual response vocabulary to
ordinal numbers and validates the resulting solution.

Run as part of ``python run_project.py``. No network access is used.
"""
from __future__ import annotations

import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs"
FIG = OUT / "figures"

# The five ordinal influence questions Q9-Q13 in the survey instrument.
FEATURES = [
    "price_sensitivity",
    "discount_importance",
    "emi_influence",
    "exchange_influence",
    "delivery_cost_influence",
]

# Legacy names from the broken pipeline are accepted, then renamed.
COLUMN_ALIASES = {
    "emi_influence_score": "emi_influence",
    "exchange_influence_score": "exchange_influence",
    "delivery_cost_influence_score": "delivery_cost_influence",
    "discount_importance_score": "discount_importance",
    "price_sensitivity_score": "price_sensitivity",
}

# Exact questionnaire response vocabulary -> ordinal score.
ORDINAL = {
    "price_sensitivity": {
        "not at all": 1, "slightly": 2, "moderately": 3, "very": 4, "extremely": 5,
    },
    "discount_importance": {
        "1": 1, "2": 2, "3": 3, "4": 4, "5": 5,
        "not important": 1, "very important": 5,
    },
    "emi_influence": {
        "not at all": 1, "a little": 2, "somewhat": 3, "a lot": 4,
    },
    "exchange_influence": {
        "not at all": 1, "a little": 2, "somewhat": 3, "a lot": 4,
    },
    "delivery_cost_influence": {
        "not at all": 1, "a little": 2, "somewhat": 3, "a lot": 4,
    },
}

# "Not applicable" / "Unsure" are non-substantive answers: treat as missing
# rather than pretending they are low influence.
MISSING_TOKENS = {
    "", "na", "n/a", "nan", "none", "null", "unsure", "not applicable",
    "not eligible", "not eligible / unsure", "not eligible/unsure",
}

DESCRIPTORS = {
    "price_sensitivity": "price-sensitive",
    "discount_importance": "discount-driven",
    "emi_influence": "EMI-responsive",
    "exchange_influence": "exchange-motivated",
    "delivery_cost_influence": "delivery-cost-sensitive",
}

SPEND_RANK = {
    "Below 1000": 1, "1000-4999": 2, "5000-14999": 3,
    "15000-29999": 4, "30000-59999": 5, "60000+": 6,
}
SPEND_LABEL = {v: k for k, v in SPEND_RANK.items()}


def _key(value) -> str:
    """Normalise a survey answer for lookup."""
    text = str(value).strip().lower()
    text = text.replace("\u2013", "-").replace("\u2014", "-")
    return re.sub(r"\s+", " ", text)


def encode_features(raw: pd.DataFrame):
    """Return (clean raw rows, encoded numeric features, encoding report)."""
    df = raw.rename(columns={c: COLUMN_ALIASES.get(c, c) for c in raw.columns}).copy()
    df = df.loc[:, ~df.columns.duplicated()]

    missing_columns = [c for c in FEATURES if c not in df.columns]
    if missing_columns:
        raise ValueError(
            "Survey is missing required column(s): " + ", ".join(missing_columns)
            + ". Expected the 14-field schema in data/survey_template.csv."
        )

    encoded = pd.DataFrame(index=df.index)
    missing_by_feature = {}
    for col in FEATURES:
        keys = df[col].map(_key)
        numeric = keys.map(ORDINAL[col])

        # Tolerate genuinely numeric input (e.g. "4", 4.0) as well as text.
        numeric = numeric.fillna(pd.to_numeric(df[col], errors="coerce"))
        numeric = numeric.mask(keys.isin(MISSING_TOKENS))
        numeric = numeric.where(numeric.between(1, 5))
        encoded[col] = numeric.astype(float)
        missing_by_feature[col] = int(numeric.isna().sum())

    valid = encoded.notna().all(axis=1)
    report = {
        "rows_read": int(len(df)),
        "rows_dropped": int((~valid).sum()),
        "rows_used": int(valid.sum()),
        "missing_by_feature": missing_by_feature,
        "columns_used": list(FEATURES),
        "renamed_legacy_columns": sorted(set(raw.columns) & set(COLUMN_ALIASES)),
    }
    return df.loc[valid].reset_index(drop=True), encoded.loc[valid].reset_index(drop=True), report


def select_k(X: np.ndarray, k_min: int = 2, k_max: int = 6, seed: int = 42):
    """Compare candidate k values with four standard internal metrics."""
    upper = min(k_max, len(X) - 1)
    rows = []
    for k in range(k_min, upper + 1):
        model = KMeans(n_clusters=k, random_state=seed, n_init=10).fit(X)
        labels = model.labels_
        rows.append({
            "k": k,
            "inertia": round(float(model.inertia_), 3),
            "silhouette": round(float(silhouette_score(X, labels)), 4),
            "calinski_harabasz": round(float(calinski_harabasz_score(X, labels)), 3),
            "davies_bouldin": round(float(davies_bouldin_score(X, labels)), 4),
        })
    table = pd.DataFrame(rows)
    best_k = int(table.loc[table["silhouette"].idxmax(), "k"])
    return table, best_k


def stability(X: np.ndarray, k: int, seed: int = 42,
              n_boot: int = 40, n_seeds: int = 20) -> dict:
    """Label agreement across random seeds and 80% bootstrap resamples.

    Adjusted Rand Index (ARI): 1.0 = identical partitions, 0 = chance-level.
    """
    reference = KMeans(n_clusters=k, random_state=seed, n_init=10).fit_predict(X)

    seed_scores = []
    for offset in range(1, n_seeds + 1):
        labels = KMeans(n_clusters=k, random_state=seed + 1000 + offset,
                        n_init=10).fit_predict(X)
        seed_scores.append(adjusted_rand_score(reference, labels))

    rng = np.random.default_rng(seed)
    boot_scores = []
    sample_size = max(k + 1, int(0.8 * len(X)))
    for offset in range(n_boot):
        idx = rng.choice(len(X), size=sample_size, replace=True)
        model = KMeans(n_clusters=k, random_state=seed + 2000 + offset,
                       n_init=10).fit(X[idx])
        # Score on the same respondents used for the reference solution.
        boot_scores.append(adjusted_rand_score(reference, model.predict(X)))

    return {
        "seed_ari_mean": round(float(np.mean(seed_scores)), 4),
        "seed_ari_min": round(float(np.min(seed_scores)), 4),
        "bootstrap_ari_mean": round(float(np.mean(boot_scores)), 4),
        "bootstrap_ari_p05": round(float(np.percentile(boot_scores, 5)), 4),
        "n_seeds": n_seeds,
        "n_bootstraps": n_boot,
    }


def permutation_test(X: np.ndarray, k: int, observed_silhouette: float,
                     seed: int = 42, n_perm: int = 100) -> dict:
    """Compare observed separation with independently permuted features."""
    rng = np.random.default_rng(seed)
    permuted_scores = []
    for offset in range(n_perm):
        shuffled = np.column_stack([rng.permutation(X[:, j]) for j in range(X.shape[1])])
        labels = KMeans(n_clusters=k, random_state=seed + 3000 + offset,
                        n_init=10).fit_predict(shuffled)
        permuted_scores.append(silhouette_score(shuffled, labels))
    permuted = np.asarray(permuted_scores)
    p_value = (1 + int(np.sum(permuted >= observed_silhouette))) / (n_perm + 1)
    return {
        "observed_silhouette": round(float(observed_silhouette), 4),
        "permuted_silhouette_mean": round(float(permuted.mean()), 4),
        "permuted_silhouette_p95": round(float(np.percentile(permuted, 95)), 4),
        "p_value": round(float(p_value), 4),
        "n_permutations": n_perm,
    }


def feature_significance(encoded: pd.DataFrame, labels: np.ndarray, k: int) -> pd.DataFrame:
    """Non-parametric per-feature tests: do segments differ on each score?"""
    rows = []
    for feature in FEATURES:
        groups = [encoded.loc[labels == index, feature].to_numpy(dtype=float)
                  for index in range(k)]
        statistic, p_value = stats.kruskal(*groups)
        grand_mean = encoded[feature].mean()
        ss_between = sum(len(group) * (group.mean() - grand_mean) ** 2 for group in groups)
        ss_total = float(((encoded[feature] - grand_mean) ** 2).sum())
        rows.append({
            "feature": feature,
            "kruskal_H": round(float(statistic), 3),
            "p_value": float(p_value),
            "eta_squared": round(float(ss_between / ss_total) if ss_total else 0.0, 3),
        })
    return pd.DataFrame(rows).sort_values("p_value").reset_index(drop=True)


def _segment_name(means: pd.Series, overall: pd.Series, spreads: pd.Series, cluster: int) -> str:
    z = (means - overall) / spreads
    elevated = sorted(
        (feature for feature in FEATURES if z[feature] >= 0.20),
        key=lambda feature: -z[feature],
    )
    if not elevated:
        return f"Segment {cluster}: cautious / low-influence buyers"
    descriptors = [DESCRIPTORS[feature] for feature in elevated[:2]]
    return f"Segment {cluster}: " + " + ".join(descriptors)


def profile_clusters(clean: pd.DataFrame, encoded: pd.DataFrame,
                     labels: np.ndarray, k: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build a respondent-level assignment table and a cluster profile table."""
    assignments = clean.copy()
    assignments["cluster"] = labels + 1

    overall = encoded.mean()
    spreads = encoded.std(ddof=1).replace(0, 1)
    profiles = []
    for cluster in range(1, k + 1):
        part = encoded.loc[labels == cluster - 1, FEATURES]
        means, stds = part.mean(), part.std(ddof=1)
        name = _segment_name(means, overall, spreads, cluster)

        spend_ranks = clean.loc[labels == cluster - 1, "spend_band_inr"].map(
            lambda value: SPEND_RANK.get(_key(value), np.nan)
        ) if "spend_band_inr" in clean else pd.Series(dtype=float)
        typical_spend = SPEND_LABEL.get(int(round(spend_ranks.median())), "n/a") \
            if spend_ranks.notna().any() else "n/a"

        row = {
            "cluster": cluster,
            "n": int((labels == cluster - 1).sum()),
            "share_pct": round(100 * (labels == cluster - 1).mean(), 1),
            "segment_label": name,
            "typical_spend_band": typical_spend,
        }
        for feature in FEATURES:
            row[feature + "_mean"] = round(float(means[feature]), 2)
            row[feature + "_sd"] = round(float(stds[feature]), 2)
        profiles.append(row)

    assignments["segment_label"] = assignments["cluster"].map(
        {row["cluster"]: row["segment_label"] for row in profiles}
    )
    return assignments, pd.DataFrame(profiles)


def _save_figures(X: np.ndarray, labels: np.ndarray, k_table: pd.DataFrame,
                  best_k: int, encoded: pd.DataFrame, profiles: pd.DataFrame,
                  report: dict, open_image) -> None:
    FIG.mkdir(parents=True, exist_ok=True)

    # k selection: silhouette and inertia side by side.
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    axes[0].plot(k_table["k"], k_table["silhouette"], marker="o", color="#39856A")
    axes[0].axvline(best_k, color="#E39C37", ls="--", lw=1.5,
                    label=f"selected k={best_k}")
    axes[0].set(xlabel="Number of clusters (k)", ylabel="Silhouette score",
                title="Cluster separation by k", ylim=(0, 1))
    axes[0].grid(alpha=.25); axes[0].legend()
    axes[1].plot(k_table["k"], k_table["inertia"], marker="s", color="#4C78A8")
    axes[1].set(xlabel="Number of clusters (k)", ylabel="Within-cluster sum of squares",
                title="Elbow (inertia) by k")
    axes[1].grid(alpha=.25)
    fig.suptitle(f"K selection — {report['rows_used']} valid survey responses")
    fig.tight_layout()
    path = FIG / "11_k_selection.png"
    fig.savefig(path, dpi=200); plt.close(fig); open_image(path)

    # Cluster profile heatmap (standardised feature means).
    matrix = np.array([
        [(profiles.loc[profiles.cluster.eq(c), f + "_mean"].iloc[0]
          - encoded[f].mean()) / encoded[f].std(ddof=1) for f in FEATURES]
        for c in sorted(profiles.cluster)
    ])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    image = ax.imshow(matrix, cmap="RdYlGn", vmin=-1.6, vmax=1.6, aspect="auto")
    ax.set_xticks(range(len(FEATURES)))
    ax.set_xticklabels(["Price\nsensitivity", "Discount\nimportance", "EMI\ninfluence",
                        "Exchange\ninfluence", "Delivery cost\ninfluence"], fontsize=9)
    ax.set_yticks(range(len(profiles)))
    ax.set_yticklabels([f"C{c} (n={int(profiles.loc[profiles.cluster.eq(c), 'n'].iloc[0])})"
                        for c in sorted(profiles.cluster)], fontsize=9)
    for row in range(matrix.shape[0]):
        for col in range(matrix.shape[1]):
            ax.text(col, row, f"{matrix[row, col]:+.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(image, ax=ax, shrink=.8, label="SD above / below survey mean")
    ax.set_title("Cluster profiles (standardised mean influence scores)")
    fig.tight_layout()
    path = FIG / "12_cluster_profiles.png"
    fig.savefig(path, dpi=200); plt.close(fig); open_image(path)

    # PCA projection of respondents.
    coords = PCA(n_components=2, random_state=42).fit_transform(X)
    fig, ax = plt.subplots(figsize=(8, 6))
    for cluster in sorted(set(labels)):
        mask = labels == cluster
        ax.scatter(coords[mask, 0], coords[mask, 1], s=42, alpha=.8,
                   label=f"Segment {cluster + 1}")
        centre = coords[mask].mean(axis=0)
        ax.scatter(*centre, marker="X", s=180, edgecolor="black", linewidth=.8, zorder=5)
    ax.set(xlabel="Principal component 1", ylabel="Principal component 2",
           title="Respondents in 2-D feature space (X = segment centre)")
    ax.grid(alpha=.2); ax.legend(fontsize=9)
    fig.tight_layout()
    path = FIG / "13_cluster_scatter.png"
    fig.savefig(path, dpi=200); plt.close(fig); open_image(path)


def run(raw: pd.DataFrame, seed: int = 42, open_image=None) -> dict:
    """Execute the full segmentation + validation pipeline and write outputs."""
    if open_image is None:
        open_image = lambda _path: None

    clean, encoded, report = encode_features(raw)
    if report["rows_used"] < 10:
        raise ValueError(
            f"Only {report['rows_used']} usable responses; at least 10 are required."
        )

    OUT.mkdir(parents=True, exist_ok=True)
    scaler = StandardScaler()
    X = scaler.fit_transform(encoded.to_numpy(dtype=float))

    k_table, best_k = select_k(X, seed=seed)
    model = KMeans(n_clusters=best_k, random_state=seed, n_init=10).fit(X)
    labels = model.labels_
    silhouette = float(silhouette_score(X, labels))

    stable = stability(X, best_k, seed=seed)
    perm = permutation_test(X, best_k, silhouette, seed=seed)
    significance = feature_significance(encoded, labels, best_k)
    assignments, profiles = profile_clusters(clean, encoded, labels, best_k)

    assignments.to_csv(OUT / "exploratory_consumer_segments.csv", index=False)
    profiles.to_csv(OUT / "cluster_profiles.csv", index=False)
    k_table.to_csv(OUT / "k_selection.csv", index=False)
    significance.to_csv(OUT / "feature_significance.csv", index=False)
    pd.DataFrame([{
        "k_selected": best_k,
        "silhouette": round(silhouette, 4),
        "calinski_harabasz": round(float(calinski_harabasz_score(X, labels)), 3),
        "davies_bouldin": round(float(davies_bouldin_score(X, labels)), 4),
        **stable, **perm, "n_respondents": report["rows_used"],
    }]).to_csv(OUT / "segment_validation.csv", index=False)

    _save_figures(X, labels, k_table, best_k, encoded, profiles, report, open_image)

    return {
        "encoding": report,
        "k_selection": k_table.to_dict(orient="records"),
        "best_k": best_k,
        "silhouette": round(silhouette, 4),
        "stability": stable,
        "permutation": perm,
        "profiles": profiles.to_dict(orient="records"),
        "feature_significance": significance.to_dict(orient="records"),
        "assignments": assignments.to_dict(orient="records"),
        "feature_means": encoded.mean().round(3).to_dict(),
        "scaler_means": dict(zip(FEATURES, scaler.mean_.round(3))),
        "scaler_scales": dict(zip(FEATURES, scaler.scale_.round(3))),
    }
