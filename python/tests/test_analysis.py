import unittest
import pandas as pd

from run_project import build_scenarios, calculate_adjacent_year_growth, load_market_data


class MarketAnalysisTests(unittest.TestCase):
    def test_growth_only_for_adjacent_years(self):
        frame = pd.DataFrame({
            "year": [2021, 2022, 2024, 2025],
            "market_value_usd_bn": [100, 110, 150, 165],
        })
        result = calculate_adjacent_year_growth(frame)
        self.assertAlmostEqual(result.loc[1, "yoy_growth_percent"], 10.0)
        self.assertTrue(pd.isna(result.loc[2, "yoy_growth_percent"]))
        self.assertAlmostEqual(result.loc[3, "yoy_growth_percent"], 10.0)

    def test_scenario_baseline_and_assumptions(self):
        result = build_scenarios()
        base_2024 = result[(result.scenario == "Base") & (result.year == 2024)].iloc[0]
        self.assertAlmostEqual(base_2024.tam_usd_bn, 27.0)
        self.assertAlmostEqual(base_2024.illustrative_sam_usd_bn, 8.1)
        self.assertAlmostEqual(base_2024.assumed_cagr_percent, 12.0)

    def test_source_data_loads_with_expected_rows(self):
        frame = load_market_data()
        self.assertIn("India total e-commerce", set(frame.market_scope))
        self.assertTrue((frame.market_value_usd_bn > 0).all())


if __name__ == "__main__":
    unittest.main()
