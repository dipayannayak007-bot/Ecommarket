"""Unit tests for the consent-aware consumer segmentation workflow.

All rows below are synthetic test fixtures created in memory. They are not
survey responses and are never written to the repository as project data.
"""
import sys
import tempfile
import unittest
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from segment_consumers import clean_column_names, prepare_survey, run_clustering


class ConsumerSegmentationTests(unittest.TestCase):
    def write_csv(self, frame, directory):
        path = Path(directory) / "test_responses.csv"
        frame.to_csv(path, index=False)
        return path

    def test_column_names_are_normalised(self):
        result = clean_column_names(["Age Band", "Preferred-Category", "Spend (INR)"])
        self.assertEqual(result, ["age_band", "preferred_category", "spend_inr"])

    def test_non_consenting_rows_are_excluded(self):
        frame = pd.DataFrame({
            "consent": ["yes", "no", "YES"],
            "age_band": ["18-24", "25-34", "18-24"],
            "preferred_category": ["Mobile", "Laptop", "Appliance"],
            "purchase_frequency_12m": [1, 2, 3],
        })
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_csv(frame, directory)
            eligible, features = prepare_survey(path)

        self.assertEqual(len(eligible), 2)
        self.assertIn("preferred_category", features)

    def test_missing_consent_column_is_rejected(self):
        frame = pd.DataFrame({
            "age_band": ["18-24"] * 12,
            "preferred_category": ["Mobile"] * 12,
            "purchase_frequency_12m": [1] * 12,
        })
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_csv(frame, directory)
            with self.assertRaisesRegex(ValueError, "consent"):
                prepare_survey(path)

    def test_small_sample_is_rejected(self):
        frame = pd.DataFrame({
            "consent": ["yes"] * 9,
            "age_band": ["18-24"] * 9,
            "preferred_category": ["Mobile"] * 9,
            "purchase_frequency_12m": [1] * 9,
        })
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_csv(frame, directory)
            with self.assertRaisesRegex(ValueError, "at least 10"):
                prepare_survey(path)

    def test_clustering_returns_assignments_profiles_and_scores(self):
        # Synthetic fixture only: varied categories and frequencies exercise
        # the pipeline without implying that real respondents were surveyed.
        frame = pd.DataFrame({
            "residence_type": ["Urban"] * 6 + ["Rural"] * 6,
            "age_band": ["18-24"] * 12,
            "preferred_category": ["Mobile"] * 6 + ["Appliance"] * 6,
            "purchase_frequency_12m": [1, 1, 2, 2, 3, 3, 1, 2, 3, 4, 4, 5],
        })
        assignments, profiles, scores = run_clustering(
            frame, list(frame.columns)
        )

        self.assertEqual(len(assignments), 12)
        self.assertIn("cluster", assignments.columns)
        self.assertIn("respondents", profiles.columns)
        self.assertIn("silhouette_score", scores.columns)
        self.assertAlmostEqual(float(profiles["share_percent"].sum()), 100.0, places=1)


if __name__ == "__main__":
    unittest.main()
