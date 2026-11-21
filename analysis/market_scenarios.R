# CNT-02: transparent TAM/SAM and scenario model
# Run from the repository root: Rscript analysis/market_scenarios.R

dir.create("outputs", showWarnings = FALSE, recursive = TRUE)

tam_2024_usd_bn <- 27
sam_reachable_share <- 0.30  # planning assumption; replace with evidence
scenario_rates <- data.frame(
  scenario = c("Conservative", "Base", "Optimistic"),
  cagr = c(0.08, 0.12, 0.16)
)

forecast <- merge(
  data.frame(year = 2024:2030),
  scenario_rates
)
forecast$market_usd_bn <- tam_2024_usd_bn *
  (1 + forecast$cagr)^(forecast$year - 2024)
forecast$sam_usd_bn <- forecast$market_usd_bn * sam_reachable_share

write.csv(forecast, "outputs/electronics_scenario_forecast.csv",
          row.names = FALSE)

cat("2024 TAM (US$bn):", tam_2024_usd_bn, "\n")
cat("Illustrative 2024 SAM (US$bn):",
    tam_2024_usd_bn * sam_reachable_share, "\n")
cat("Wrote outputs/electronics_scenario_forecast.csv\n")
