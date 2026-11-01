# Data directory

## Files and intended use
- survey_template.csv: blank schema for primary survey responses.
- survey_responses.csv: create locally from consented, anonymised responses; excluded from Git.
- transactions.csv: optional permitted India transaction extract; excluded from Git.
- raw/ and processed/: local source data; do not commit restricted or large microdata.

## Transaction CSV schema
order_id, customer_id, order_date, category, product, quantity, unit_price_inr, discount_inr, state

Use ISO dates (YYYY-MM-DD), numeric quantity/prices and anonymised customer IDs. Document data owner, collection period, sampling frame, licence and cleaning rules.

## Official HCES data
MoSPI HCES 2023-24 catalogue:
https://microdata.gov.in/NADA/index.php/catalog/CEXP

Read the data-use rider and catalogue terms. Public-use access does not automatically mean unrestricted redistribution. Do not upload microdata to this repository. HCES measures household expenditure; it is not a direct measure of online orders.

## Survey schema
respondent_id, state_ut, residence_type, age_band, online_purchase_12m, preferred_category, purchase_frequency_12m, spend_band_inr, price_sensitivity, discount_importance, emi_influence, exchange_influence, delivery_cost_influence, consent

Keep respondent_id anonymous. Do not collect names, phone numbers, exact addresses or payment credentials.
