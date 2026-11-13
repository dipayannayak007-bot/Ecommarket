"""Run exploratory consumer clustering on real, consented survey responses.

This script refuses to invent observations. It excludes non-consenting records,
uses only the survey's available behaviour/demographic fields, and writes
cluster assignments and profiles for exploratory interpretation.

Run from the python/ directory:
    python segment_consumers.py --input data/survey_responses.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path
import re
import sys

import pandas as pd
from sklearn.cluster import KMeans
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.metrics import silhouette_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "reports" / "segmentation"
REQUIRED = {"consent"}
FEATURES = [
    "residence_type", "age_band", "online_purchase_12m",
    "preferred_category", "purchase_frequency_12m", "spend_band_inr",
    "price_sensitivity", "discount_importance", "emi_influence",
    "exchange_influence", "delivery_cost_influence",
]


def clean_column_names(columns) -> list[str]:
    return [re.sub(r"[^a-z0-9]+", "_", str(c).strip().lower()).strip("_")
            for c in columns]


def prepare_survey(path: Path) -> tuple[pd.DataFrame, list[str]]:
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. Add real, consented survey responses first."
        )
    df = pd.read_csv(path)
    df.columns = clean_column_names(df.columns)
    missing = REQUIRED.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required consent column(s): {sorted(missing)}")

    consent = df["consent"].astype(str).str.strip().str.lower()
    eligible = consent.isin({"yes", "y", "true", "1", "consented"})
    df = df.loc[eligible].copy()
    available = [c for c in FEATURES if c in df.columns]
    if len(available) < 3:
        raise ValueError(
            "At least three supported survey feature columns are required."
        )
    if df.empty:
        raise ValueError("No consented responses found; no clustering performed.")

    # Drop fields with no usable observations and rows with no feature data.
    available = [c for c in available if df[c].notna().any()]
    X = df[available].copy()
    X = X.replace(r"^\s*$", pd.NA, regex=True)
    valid_rows = X.notna().any(axis=1)
    df, X = df.loc[valid_rows].copy(), X.loc[valid_rows].copy()
    if len(X) < 10:
        raise ValueError(
            f"Only {len(X)} usable consented responses. Collect at least 10 "
            "for this exploratory workflow; larger, well-designed samples are "
            "strongly preferred. No clusters were produced."
        )
    return df.reset_index(drop=True), available


def run_clustering(df: pd.DataFrame, features: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    X = df[features].copy()
    numeric = [c for c in features if pd.api.types.is_numeric_dtype(X[c])]
    categorical = [c for c in features if c not in numeric]

    transformers = []
    if numeric:
        numeric_pipe = Pipeline([
            ("impute", SimpleImputer(strategy="median")),
            ("scale", StandardScaler()),
        ])
        transformers.append(("numeric", numeric_pipe, numeric))
    if categorical:
        categorical_pipe = Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ])
        transformers.append(("categorical", categorical_pipe, categorical))

    preprocess = ColumnTransformer(transformers=transformers)
    matrix = preprocess.fit_transform(X)
    n = len(df)
    max_k = min(6, n - 1)
    if max_k < 2:
        raise ValueError("Not enough observations to evaluate two clusters.")

    scores = []
    best = None
    for k in range(2, max_k + 1):
        model = KMeans(n_clusters=k, random_state=42, n_init=20)
        labels = model.fit_predict(matrix)
        if len(set(labels)) < 2:
            continue
        score = float(silhouette_score(matrix, labels))
        scores.append({"clusters": k, "silhouette_score": score})
        if best is None or score > best[0]:
            best = (score, labels, k)

    if best is None:
        raise ValueError("Could not form valid clusters from these responses.")

    assignments = df.copy()
    assignments["cluster"] = best[1] + 1
    assignments["cluster"] = assignments["cluster"].astype(int)
    profiles = assignments.groupby("cluster").agg(
        respondents=("cluster", "size")
    ).reset_index()
    # Add transparent modal/median descriptors for interpretation.
    for col in features:
        if pd.api.types.is_numeric_dtype(assignments[col]):
            summary = assignments.groupby("cluster")[col].median()
        else:
            summary = assignments.groupby("cluster")[col].agg(
                lambda s: s.mode(dropna=True).iloc[0]
                if not s.mode(dropna=True).empty else pd.NA
            )
        profiles[col + "_profile"] = profiles["cluster"].map(summary)
    profiles["share_percent"] = (
        profiles.respondents / len(assignments) * 100
    ).round(1)
    print(
        f"Selected k={best[2]} using the highest silhouette score "
        f"({best[0]:.3f}) among tested k=2..{max_k}."
    )
    print("Cluster labels are exploratory; interpret profiles before naming segments.")
    return assignments, profiles, pd.DataFrame(scores)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=ROOT / "data" / "survey_responses.csv")
    args = parser.parse_args()
    try:
        survey, features = prepare_survey(args.input)
        assignments, profiles, scores = run_clustering(survey, features)
    except (FileNotFoundError, ValueError) as exc:
        print(f"STOP: {exc}", file=sys.stderr)
        return 2

    OUTPUT.mkdir(parents=True, exist_ok=True)
    assignments.to_csv(OUTPUT / "cluster_assignments.csv", index=False)
    profiles.to_csv(OUTPUT / "cluster_profiles.csv", index=False)
    scores.to_csv(OUTPUT / "silhouette_scores.csv", index=False)
    print(f"Saved exploratory results to {OUTPUT}")
    print("Do not generalise a convenience sample to India's population.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
