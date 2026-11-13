"""
CFPB complaints: January 2025 spike baseline + monetary-relief rates by product.

Reads the dbt marts in BigQuery (default) or, for offline reproduction, the raw
CSV prepared by 00_prepare_for_bigquery.py (--source csv). Both paths build the
same dataframe, so results should match; the BigQuery path is what the project uses.

Writes small aggregate CSVs to exports/ (used by the Power BI dashboard).

Usage:
    python python/01_spike_and_relief_analysis.py                    # BigQuery
    python python/01_spike_and_relief_analysis.py --source csv       # offline check

Method notes (see README for limitations):
  * Baseline = the company's mean monthly complaint count over the OTHER five months in the
    window (Oct 2024 - Mar 2025). The data has no earlier history, so this is a
    within-window comparison, not a year-over-year one.
  * Spike test = one-sided Poisson tail probability of seeing >= the January count given the
    baseline mean, Bonferroni-corrected across the companies tested. Complaint counts are
    over-dispersed, so treat p-values as a screening tool; the ratio and excess volume are the
    headline numbers.
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
EXPORTS = ROOT / "exports"
CSV_PATH = ROOT / "data" / "interim" / "complaints_bq.csv"
SPIKE_MONTH = pd.Timestamp("2025-01-01")
MIN_SPIKE_COMPLAINTS = 100          # only test companies with a meaningful January volume
EXPECTED_ROWS = 96155


def load_from_bigquery(project: str) -> pd.DataFrame:
    from google.cloud import bigquery

    client = bigquery.Client(project=project)
    sql = f"""
        select f.complaint_id, f.date_day as received_date, c.company_name as company,
               p.product, f.got_monetary_relief
        from `{project}.cfpb_analytics.fct_complaints` f
        join `{project}.cfpb_analytics.dim_company` c using (company_key)
        join `{project}.cfpb_analytics.dim_product` p using (product_key)
    """
    return client.query(sql).to_dataframe()


def load_from_csv() -> pd.DataFrame:
    raw = pd.read_csv(CSV_PATH, dtype=str)
    out = pd.DataFrame({
        "complaint_id": raw["complaint_id"].astype("int64"),
        "received_date": pd.to_datetime(raw["date_received"], utc=True).dt.tz_localize(None).dt.normalize(),
        "company": raw["company"].str.strip(),
        "product": raw["product"].str.strip(),
        "got_monetary_relief": raw["company_response_to_consumer"].str.strip().eq("Closed with monetary relief"),
    })
    return out


def wilson_interval(successes: int, n: int, confidence: float = 0.95):
    z = stats.norm.ppf(0.5 + confidence / 2)
    p = successes / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return centre - half, centre + half


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["bigquery", "csv"], default="bigquery")
    parser.add_argument("--project", default="cfpb-complaint-analytics")
    args = parser.parse_args()

    df = load_from_bigquery(args.project) if args.source == "bigquery" else load_from_csv()
    df["received_date"] = pd.to_datetime(df["received_date"])
    df["month"] = df["received_date"].dt.to_period("M").dt.to_timestamp()
    assert len(df) == EXPECTED_ROWS, f"expected {EXPECTED_ROWS} rows, got {len(df)}"
    assert df["complaint_id"].is_unique
    EXPORTS.mkdir(exist_ok=True)
    months = sorted(df["month"].unique())
    print(f"Rows: {len(df):,}   Window: {df['received_date'].min().date()} to {df['received_date'].max().date()}")

    # ---- 1. Monthly volume and the January spike -------------------------------------------
    monthly = df.groupby("month").size().rename("complaints").reset_index()
    monthly["pct_change_vs_prev_month"] = monthly["complaints"].pct_change() * 100
    monthly.to_csv(EXPORTS / "monthly_complaints.csv", index=False)
    print("\nMonthly complaints:\n", monthly.to_string(index=False))
    jan = int(monthly.loc[monthly["month"] == SPIKE_MONTH, "complaints"].iloc[0])
    dec = int(monthly.loc[monthly["month"] == SPIKE_MONTH - pd.DateOffset(months=1), "complaints"].iloc[0])
    print(f"\nJan vs Dec: {jan:,} vs {dec:,} = {100 * (jan / dec - 1):+.0f}%")

    # ---- 2. Company-level baseline test ------------------------------------------------------
    cm = df.groupby(["company", "month"]).size().unstack(fill_value=0).reindex(columns=months, fill_value=0)
    other = [m for m in months if m != SPIKE_MONTH]
    spike = pd.DataFrame({
        "january_complaints": cm[SPIKE_MONTH],
        "baseline_monthly_mean": cm[other].mean(axis=1),
        "total_complaints": cm.sum(axis=1),
    })
    spike["excess_complaints"] = spike["january_complaints"] - spike["baseline_monthly_mean"]
    spike["ratio_vs_baseline"] = spike["january_complaints"] / spike["baseline_monthly_mean"].replace(0, np.nan)
    tested = spike[spike["january_complaints"] >= MIN_SPIKE_COMPLAINTS].copy()
    tested["poisson_p"] = stats.poisson.sf(tested["january_complaints"] - 1, tested["baseline_monthly_mean"])
    tested["bonferroni_p"] = np.minimum(tested["poisson_p"] * len(tested), 1.0)
    total_excess = spike["excess_complaints"].clip(lower=0).sum()
    tested["share_of_total_excess"] = tested["excess_complaints"].clip(lower=0) / total_excess
    tested = tested.sort_values("excess_complaints", ascending=False)
    tested.round(4).reset_index().to_csv(EXPORTS / "company_spike_baseline.csv", index=False)
    print(f"\nCompanies with >= {MIN_SPIKE_COMPLAINTS} January complaints: {len(tested)}")
    print("Top 8 by excess volume:\n", tested.head(8)[[
        "january_complaints", "baseline_monthly_mean", "ratio_vs_baseline", "excess_complaints",
        "bonferroni_p", "share_of_total_excess"]].round(3).to_string())

    # ---- 3. Does the spike survive removing the flagged companies? ---------------------------
    flagged = tested[tested["bonferroni_p"] < 0.01].head(2).index.tolist()
    rest = df[~df["company"].isin(flagged)].groupby("month").size()
    rest_jan, rest_dec = rest[SPIKE_MONTH], rest[SPIKE_MONTH - pd.DateOffset(months=1)]
    print(f"\nFlagged (top 2 significant by excess): {flagged}")
    print(f"Jan vs Dec excluding them: {rest_jan:,} vs {rest_dec:,} = {100 * (rest_jan / rest_dec - 1):+.0f}%")
    flagged_excess = tested.loc[flagged, "excess_complaints"].sum()
    print(f"Their combined excess = {flagged_excess:,.0f} complaints = {100 * flagged_excess / total_excess:.0f}% of all company-level excess")

    top10 = df.groupby("company").size().nlargest(10).index
    df.assign(company_group=np.where(df["company"].isin(top10), df["company"], "All other companies")) \
      .groupby(["month", "company_group"]).size().rename("complaints").reset_index() \
      .to_csv(EXPORTS / "monthly_complaints_by_company.csv", index=False)

    # ---- 4. Monetary relief rate by product --------------------------------------------------
    by_prod = df.groupby("product")["got_monetary_relief"].agg(complaints="size", monetary_relief="sum").reset_index()
    by_prod["relief_rate"] = by_prod["monetary_relief"] / by_prod["complaints"]
    ci = [wilson_interval(int(r.monetary_relief), int(r.complaints)) for r in by_prod.itertuples()]
    by_prod["ci95_low"], by_prod["ci95_high"] = zip(*ci)
    table = pd.crosstab(df["product"], df["got_monetary_relief"])
    chi2, p, dof, _ = stats.chi2_contingency(table)
    n = table.to_numpy().sum()
    cramers_v = np.sqrt(chi2 / (n * (min(table.shape) - 1)))
    by_prod.to_csv(EXPORTS / "monetary_relief_by_product.csv", index=False)
    print("\nMonetary relief by product (Wilson 95% CI):\n",
          by_prod.assign(**{c: (by_prod[c] * 100).round(1) for c in ["relief_rate", "ci95_low", "ci95_high"]}).to_string(index=False))
    print(f"Chi-square product x relief: chi2={chi2:,.1f}, dof={dof}, p={p:.3g}, Cramer's V={cramers_v:.3f}")
    overall = df["got_monetary_relief"].mean()
    print(f"Overall monetary relief rate: {100 * overall:.1f}%")

    by_pm = df.groupby(["month", "product"])["got_monetary_relief"].agg(complaints="size", monetary_relief="sum").reset_index()
    by_pm["relief_rate"] = by_pm["monetary_relief"] / by_pm["complaints"]
    by_pm.to_csv(EXPORTS / "monetary_relief_by_product_month.csv", index=False)
    print(f"\nWrote aggregate CSVs to {EXPORTS}")


if __name__ == "__main__":
    main()
