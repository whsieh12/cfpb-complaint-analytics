"""
00_prepare_for_bigquery.py

Copies the raw CFPB CSV to data/interim/complaints_bq.csv with ONE change: the header row is renamed to
snake_case names that BigQuery accepts (no spaces, hyphens or question marks). No data row is changed.
The row count is checked before and after.

Run from the repo root:   python python/00_prepare_for_bigquery.py
"""
import csv
from pathlib import Path

RAW = Path("data/raw/complaints-2026-10-13_22_06.csv")
OUT = Path("data/interim/complaints_bq.csv")

RENAME = {
    "Date received": "date_received",
    "Product": "product",
    "Sub-product": "sub_product",
    "Issue": "issue",
    "Sub-issue": "sub_issue",
    "Company public response": "company_public_response",
    "Company": "company",
    "State": "state",
    "ZIP code": "zip_code",
    "Tags": "tags",
    "Submitted via": "submitted_via",
    "Date sent to company": "date_sent_to_company",
    "Company response to consumer": "company_response_to_consumer",
    "Timely response?": "timely_response",
    "Complaint ID": "complaint_id",
}

csv.field_size_limit(10**8)
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(RAW, newline="", encoding="utf-8-sig") as src, open(OUT, "w", newline="", encoding="utf-8") as dst:
    reader, writer = csv.reader(src), csv.writer(dst)
    header = next(reader)
    missing = [h for h in header if h not in RENAME]
    assert not missing, f"unexpected columns: {missing}"
    writer.writerow([RENAME[h] for h in header])
    n = 0
    for row in reader:
        assert len(row) == len(header), f"row {n + 2} has {len(row)} fields"
        writer.writerow(row)
        n += 1
print(f"wrote {OUT} with {n:,} data rows (expected 96,155)")
assert n == 96155
