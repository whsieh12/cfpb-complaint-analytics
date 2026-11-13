# Data provenance

The raw file is NOT committed to Git. To reproduce, download it yourself (steps below).

| Item | Value |
|---|---|
| Source | CFPB Consumer Complaint Database, Consumer Financial Protection Bureau |
| Source page | https://www.consumerfinance.gov/data-research/consumer-complaints/ |
| Slice used | Date received 2024-10-01 through 2025-03-31; products: Checking or savings account, Credit card, Mortgage |
| Downloaded | 2026-10-13 (from the file name timestamp) |
| File name | `complaints-2026-10-13_22_06.csv` (place in `data/raw/`) |
| Size | 29,240,660 bytes |
| Rows / columns | 96,155 / 15 (96,155 distinct Complaint IDs) |
| Row counts by product | Checking or savings account 43,554; Credit card 41,509; Mortgage 11,092 |
| SHA-256 | `d5fcc0be10c85efbcfcf5322925fa8ef49e9d47083bf9eec7705e6fa38912f8e` |
| License / terms | No named license. The CFPB page says the complaint data is "freely available for anyone to use, analyze, and build on." Cite the CFPB as the source. |

Notes
- The database updates daily, so a later download of the same filters may differ (late-arriving complaints, status updates). Compare the hash above.
- The CFPB says the data is not a statistical sample and is not representative of all consumers' experiences. Complaint counts reflect company size and customer base, not only service quality.
- This file has no complaint narrative column and no "consumer disputed" column.
- Do not open or re-save the CSV in Excel (date reformatting).
