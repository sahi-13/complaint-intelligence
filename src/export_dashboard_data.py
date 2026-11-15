"""
Export small, dashboard-ready CSV files from the SQLite database.

Run from VS Code (Run button) or:  python src/export_dashboard_data.py
Output folder: dashboard/data/   (Tableau Public and Power BI cannot read SQLite directly,
so the dashboard is built from these CSV files)

Files created
    monthly_by_product.csv      counts per month and product (for trends, KPI tiles)
    company_product_summary.csv one row per company and product, with rates
    issues_by_product.csv       top 15 issues per product
    outliers_all_metrics.csv    results of stats_tests.py (needs: stats_tests.py --all --robust --quiet)
    annotations.csv             notes to place on charts (e.g. the January 2025 surge)

Important for the dashboard: monthly_by_product.csv holds COUNTS only. Compute rates as
SUM(numerator) / SUM(denominator). Averaging per-row percentages gives wrong answers.
"""
import argparse
import sqlite3
from pathlib import Path

import pandas as pd

from stats_tests import EXCLUDE, PRODUCTS, _ANY_RELIEF, _CLOSED, _MONETARY

ROOT = Path(__file__).resolve().parent.parent

COUNTS_SQL = f"""
    COUNT(*) AS complaints,
    SUM(CASE WHEN {_CLOSED} THEN 1 ELSE 0 END) AS closed,
    SUM(CASE WHEN {_MONETARY} THEN 1 ELSE 0 END) AS monetary_relief,
    SUM(CASE WHEN {_ANY_RELIEF} THEN 1 ELSE 0 END) AS any_relief,
    SUM(timely_flag) AS timely
"""


def add_rates(df: pd.DataFrame) -> pd.DataFrame:
    closed = df["closed"].where(df["closed"] > 0)
    df["monetary_relief_pct"] = (100 * df["monetary_relief"] / closed).round(2)
    df["any_relief_pct"] = (100 * df["any_relief"] / closed).round(2)
    df["timely_pct"] = (100 * df["timely"] / df["complaints"]).round(2)
    return df


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "complaints.db"))
    ap.add_argument("--out-dir", default=str(ROOT / "dashboard" / "data"))
    ap.add_argument("--reports-dir", default=str(ROOT / "reports"))
    ap.add_argument("--min-company-complaints", type=int, default=200,
                    help="Smallest company-product group to include (keeps the file small)")
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    written = []

    with sqlite3.connect(args.db) as conn:
        # 1) Monthly trend by product (counts only)
        monthly = pd.read_sql_query(
            f"SELECT year_month, product, {COUNTS_SQL} FROM complaints "
            "GROUP BY year_month, product ORDER BY year_month, product", conn)
        latest = monthly["year_month"].max()
        monthly["is_partial_month"] = (monthly["year_month"] == latest).astype(int)
        monthly.to_csv(out / "monthly_by_product.csv", index=False)
        written.append(("monthly_by_product.csv", len(monthly)))

        # 2) Company x product summary
        cp = pd.read_sql_query(
            f"SELECT product, company, {COUNTS_SQL} FROM complaints "
            "GROUP BY product, company HAVING COUNT(*) >= ? ORDER BY product, complaints DESC",
            conn, params=(args.min_company_complaints,))
        cp = add_rates(cp)
        excluded = cp["company"].apply(lambda c: any(e in c for e in EXCLUDE))
        cp["in_benchmark"] = ((cp["product"].isin(PRODUCTS)) & (cp["closed"] >= 1000) & ~excluded).astype(int)
        cp.to_csv(out / "company_product_summary.csv", index=False)
        written.append(("company_product_summary.csv", len(cp)))

        # 3) Top issues per product
        issues = pd.read_sql_query(
            f"SELECT product, issue, {COUNTS_SQL} FROM complaints GROUP BY product, issue", conn)
        issues = (issues.sort_values(["product", "complaints"], ascending=[True, False])
                  .groupby("product").head(15))
        issues = add_rates(issues)
        issues.to_csv(out / "issues_by_product.csv", index=False)
        written.append(("issues_by_product.csv", len(issues)))

    # 4) Outlier results from stats_tests.py
    frames = []
    for metric in ["relief", "any_relief", "timely"]:
        p = Path(args.reports_dir) / f"industry_outliers_{metric}_robust.csv"
        if p.exists():
            df = pd.read_csv(p)
            df.insert(0, "metric", metric)
            frames.append(df)
    if frames:
        pd.concat(frames).to_csv(out / "outliers_all_metrics.csv", index=False)
        written.append(("outliers_all_metrics.csv", sum(len(f) for f in frames)))
    else:
        print("Note: no outlier files found. Run:  python src/stats_tests.py --all --robust --quiet")

    # 5) Chart annotations (facts taken from the data, no cause claimed)
    pd.DataFrame([
        {"year_month": "2025-01",
         "note": "Surge concentrated on Block (Cash App) and Early Warning Services (Zelle) complaints, Jan 15-24"},
        {"year_month": latest,
         "note": "Latest month is incomplete; complaints are still being added"},
    ]).to_csv(out / "annotations.csv", index=False)
    written.append(("annotations.csv", 2))

    for name, rows in written:
        size_kb = (out / name).stat().st_size / 1024
        print(f"{name:32s} {rows:>7,} rows  {size_kb:>8,.0f} KB")
    print(f"\nSaved in {out}")


if __name__ == "__main__":
    main()