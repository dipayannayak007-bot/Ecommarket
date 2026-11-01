# CNT-02: create charts for the India e-commerce project
# Run from the repository root: Rscript analysis/create_visuals.R
# Requires ggplot2, dplyr, readr, scales and tidyr.

packages <- c("ggplot2", "dplyr", "readr", "scales", "tidyr")
missing <- packages[!vapply(packages, requireNamespace, logical(1), quietly = TRUE)]
if (length(missing)) {
  stop("Install missing packages first: ", paste(missing, collapse = ", "))
}
invisible(lapply(packages, library, character.only = TRUE))

dir.create("outputs/figures", recursive = TRUE, showWarnings = FALSE)

# 1. Published national e-commerce market trend (US$ billion).
market <- tibble::tibble(
  year = c(2021, 2022, 2023, 2024, 2025, 2026, 2030, 2035),
  market_usd_bn = c(67, 84, 102, 125, 145, 163, 345, 550),
  status = c(rep("Reported", 4), rep("Forecast", 4))
)
p1 <- ggplot(market, aes(year, market_usd_bn, linetype = status)) +
  geom_line(linewidth = 1, colour = "#2463A6") +
  geom_point(size = 2.8, colour = "#2463A6") +
  scale_x_continuous(breaks = market$year) +
  scale_y_continuous(labels = scales::label_dollar(prefix = "$", suffix = "bn")) +
  labs(title = "India e-commerce market growth",
       subtitle = "IBEF, August 2025; forecast years are marked separately",
       x = "Year", y = "Market value", linetype = "Status") +
  theme_minimal(base_size = 12)
ggsave("outputs/figures/01_india_market_trend.png", p1,
       width = 9, height = 5.5, dpi = 300)

# 2. NITI Aayog category benchmarks. Categories are kept distinct.
category <- tibble::tibble(
  category = c("Smartphones", "Electronics & appliances"),
  market_usd_bn = c(39, 27)
)
p2 <- ggplot(category, aes(reorder(category, market_usd_bn), market_usd_bn)) +
  geom_col(fill = "#39856A", width = 0.65) +
  geom_text(aes(label = paste0("$", market_usd_bn, "bn")),
            hjust = -0.15, size = 4) +
  coord_flip() +
  scale_y_continuous(limits = c(0, 45), labels = scales::label_dollar(suffix = "bn")) +
  labs(title = "Selected online electronics categories in India",
       subtitle = "NITI Aayog, 2024 estimates; categories are not added together",
       x = NULL, y = "Market value") +
  theme_minimal(base_size = 12)
ggsave("outputs/figures/02_category_benchmark.png", p2,
       width = 9, height = 5.5, dpi = 300)

# 3. Category TAM scenarios (assumptions, not official forecasts).
scenario_rates <- tibble::tibble(
  scenario = c("Conservative", "Base", "Optimistic"),
  cagr = c(0.08, 0.12, 0.16)
)
scenario <- tidyr::crossing(year = 2024:2030, scenario_rates) |>
  dplyr::mutate(tam_usd_bn = 27 * (1 + cagr)^(year - 2024))
p3 <- ggplot(scenario, aes(year, tam_usd_bn, colour = scenario)) +
  geom_line(linewidth = 1.1) + geom_point(size = 2) +
  scale_x_continuous(breaks = 2024:2030) +
  scale_y_continuous(labels = scales::label_dollar(prefix = "$", suffix = "bn")) +
  labs(title = "Electronics & appliances: illustrative growth scenarios",
       subtitle = "US$27bn 2024 baseline; assumed annual growth of 8%, 12% and 16%",
       x = "Year", y = "Projected TAM", colour = "Scenario") +
  theme_minimal(base_size = 12)
ggsave("outputs/figures/03_tam_scenarios.png", p3,
       width = 9, height = 5.5, dpi = 300)

# 4. TAM versus illustrative SAM (30% reachability assumption).
sizing <- tibble::tibble(
  metric = factor(c("TAM", "Illustrative SAM"), levels = c("TAM", "Illustrative SAM")),
  value_usd_bn = c(27, 27 * 0.30)
)
p4 <- ggplot(sizing, aes(metric, value_usd_bn, fill = metric)) +
  geom_col(width = 0.6, show.legend = FALSE) +
  geom_text(aes(label = paste0("$", round(value_usd_bn, 1), "bn")),
            vjust = -0.5, size = 4) +
  scale_y_continuous(limits = c(0, 32), labels = scales::label_dollar(suffix = "bn")) +
  labs(title = "2024 market sizing: TAM and illustrative SAM",
       subtitle = "SAM uses an assumed 30% serviceable share, not a measured market share",
       x = NULL, y = "Market value") +
  theme_minimal(base_size = 12)
ggsave("outputs/figures/04_tam_sam.png", p4,
       width = 8, height = 5.5, dpi = 300)

# 5. Optional empirical charts: generated only when real data files exist.
tx_path <- "data/transactions.csv"
if (file.exists(tx_path) && file.info(tx_path)$size > 0) {
  tx <- readr::read_csv(tx_path, show_col_types = FALSE)
  required <- c("quantity", "unit_price_inr")
  if (all(required %in% names(tx))) {
    tx <- tx |>
      dplyr::mutate(gross_value_inr = quantity * unit_price_inr,
                    discount_inr = if ("discount_inr" %in% names(tx)) discount_inr else 0,
                    net_value_inr = gross_value_inr - dplyr::coalesce(discount_inr, 0)) |>
      dplyr::filter(is.finite(net_value_inr), net_value_inr >= 0)
    if (nrow(tx) > 0) {
      p5 <- ggplot(tx, aes(net_value_inr)) +
        geom_histogram(bins = 30, fill = "#4C78A8", colour = "white") +
        scale_x_continuous(labels = scales::label_number(big.mark = ",")) +
        labs(title = "Distribution of transaction values",
             subtitle = "Histogram from supplied transaction data only",
             x = "Net transaction value (INR)", y = "Number of transactions") +
        theme_minimal(base_size = 12)
      ggsave("outputs/figures/05_transaction_value_histogram.png", p5,
             width = 9, height = 5.5, dpi = 300)
    }
  } else {
    message("Transactions file found, but quantity and unit_price_inr are required for the histogram.")
  }
} else {
  message("No transaction data supplied: skipping empirical transaction histogram.")
}

survey_path <- "data/survey_responses.csv"
if (file.exists(survey_path) && file.info(survey_path)$size > 0) {
  survey <- readr::read_csv(survey_path, show_col_types = FALSE)
  if ("purchase_frequency_12m" %in% names(survey)) {
    freq <- survey |>
      dplyr::filter(!is.na(purchase_frequency_12m)) |>
      dplyr::count(purchase_frequency_12m)
    if (nrow(freq) > 0) {
      p6 <- ggplot(freq, aes(reorder(purchase_frequency_12m, n), n)) +
        geom_col(fill = "#E39C37") + coord_flip() +
        labs(title = "Online purchase frequency in the last 12 months",
             subtitle = "Unweighted survey responses; interpret according to sample design",
             x = "Purchase frequency", y = "Respondents") +
        theme_minimal(base_size = 12)
      ggsave("outputs/figures/06_purchase_frequency.png", p6,
             width = 9, height = 5.5, dpi = 300)
    }
  }
  if ("spend_band_inr" %in% names(survey)) {
    spend <- survey |>
      dplyr::filter(!is.na(spend_band_inr), spend_band_inr != "")
    if (nrow(spend) > 0) {
      p7 <- ggplot(spend, aes(spend_band_inr)) +
        geom_bar(fill = "#8064A2") + coord_flip() +
        labs(title = "Respondent spending bands",
             subtitle = "Survey responses; categorical bands, not a continuous histogram",
             x = "Self-reported spend band (INR)", y = "Respondents") +
        theme_minimal(base_size = 12)
      ggsave("outputs/figures/07_spending_bands.png", p7,
             width = 9, height = 5.5, dpi = 300)
    }
  }
} else {
  message("No survey responses supplied: skipping empirical consumer charts.")
}

cat("Charts saved in outputs/figures/. Published benchmark charts are separate from optional empirical charts.\n")
