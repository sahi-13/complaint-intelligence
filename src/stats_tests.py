"""
Which companies are genuine outliers? Company-neutral benchmark with statistical tests.

Run from VS Code (Run button) or from the terminal:
    python src/stats_tests.py                              industry scan, monetary relief
    python src/stats_tests.py --metric any_relief          monetary OR non-monetary relief
    python src/stats_tests.py --metric timely --robust     timeliness, outlier-proof baseline
    python src/stats_tests.py --company "WELLS FARGO"      report for any one company
    python src/stats_tests.py --all --robust --quiet       build all three result files silently
    python src/stats_tests.py --min-complaints 500         lower the size cut-off for peers

Metrics
    relief      share of CLOSED complaints ending with monetary relief
    any_relief  share of CLOSED complaints ending with monetary or non-monetary relief
    timely      share of ALL complaints answered on time
  'Closed' = closed with explanation / non-monetary relief / monetary relief.
  Complaints still 'In progress' or 'Untimely response' have no outcome yet and are left out
  of the relief metrics.

How it works (per product):
    1. Count complaints (n) and 'successes' (x) for every company
    2. Build a PEER POOL: companies with enough complaints, minus the exclusions below
    3. Compare each company with a BASELINE built from the pool (two-proportion z-test),
       with Wilson 95% confidence intervals
    4. Flag a company only if the result is significant after correcting for the number of
       companies tested (Bonferroni) AND the gap is at least --min-gap points.

Baseline
    default   all other companies in the pool, pooled together
    --robust  only 'typical' companies: those whose rate is close to the median company rate.
              One extreme company (e.g. a servicer with 39% timeliness) otherwise drags the
              average down and makes every normal company look 'HIGHER'.
"""
import argparse
import math
import sqlite3
from pathlib import Path

import pandas as pd
from scipy.stats import norm

ROOT = Path(__file__).resolve().parent.parent

PRODUCTS = [
    "Credit card",
    "Checking or savings account",
    "Mortgage",
    "Vehicle loan or lease",
    "Student loan",
    "Prepaid card",
]

# Companies that are NOT comparable to banks. Edit as you see fit,
# and document your choices in the README.
EXCLUDE = [
    "EQUIFAX", "TRANSUNION", "EXPERIAN",                 # credit bureaus
    "BLOCK, INC.", "EARLY WARNING SERVICES", "PAYPAL",   # payment apps / networks
    "FIDELITY NATIONAL INFORMATION", "FINCO SERVICES",   # processors / intermediaries
    "SERVICER UNDER CONTRACT",                           # generic placeholder entity
]

_CLOSED = "LOWER(company_response) IN ('closed with explanation','closed with non-monetary relief','closed with monetary relief')"
_MONETARY = "LOWER(company_response) = 'closed with monetary relief'"
_ANY_RELIEF = "LOWER(company_response) IN ('closed with monetary relief','closed with non-monetary relief')"

# metric -> (SQL for n, SQL for x, description)
METRICS = {
    "relief": (f"SUM(CASE WHEN {_CLOSED} THEN 1 ELSE 0 END)",
               f"SUM(CASE WHEN {_MONETARY} THEN 1 ELSE 0 END)",
               "monetary-relief rate (share of closed complaints)"),
    "any_relief": (f"SUM(CASE WHEN {_CLOSED} THEN 1 ELSE 0 END)",
                   f"SUM(CASE WHEN {_ANY_RELIEF} THEN 1 ELSE 0 END)",
                   "any-relief rate, monetary or non-monetary (share of closed complaints)"),
    "timely": ("COUNT(*)", "SUM(timely_flag)", "timely-response rate (all complaints)"),
}


def wilson_ci(x: int, n: int, z: float = 1.96):
    """95% confidence interval for a proportion (robust for small or extreme rates)."""
    p = x / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(centre - half, 0.0), min(centre + half, 1.0)


def two_prop_ztest(x1: int, n1: int, x2: int, n2: int):
    """Two-sided z-test for the difference between two proportions."""
    p1, p2 = x1 / n1, x2 / n2
    pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n1 + 1 / n2))
    if se == 0:
        return p1 - p2, 0.0, 1.0
    z = (p1 - p2) / se
    return p1 - p2, z, 2 * (1 - norm.cdf(abs(z)))


def typical_pool(pool: pd.DataFrame, min_gap: float) -> pd.DataFrame:
    """Keep companies whose rate is close to the median company rate (drops extreme outliers)."""
    rate = pool["x"] / pool["n"]
    med = rate.median()
    mad = (rate - med).abs().median()                    # median absolute deviation
    cutoff = max(3 * 1.4826 * mad, min_gap / 100)        # never tighter than the minimum gap
    typical = pool[(rate - med).abs() <= cutoff]
    return typical if len(typical) >= 2 else pool


def compare(row, baseline):
    """Compare one company's counts with the pooled baseline (excluding the company itself)."""
    rest = baseline[baseline["company"] != row["company"]]
    n1, x1 = int(row["n"]), int(row["x"])
    n2, x2 = int(rest["n"].sum()), int(rest["x"].sum())
    if n1 == 0 or n2 == 0:
        return None
    diff, z, p = two_prop_ztest(x1, n1, x2, n2)
    lo, hi = wilson_ci(x1, n1)
    return {
        "company": row["company"],
        "complaints": n1,
        "rate_pct": round(100 * x1 / n1, 2),
        "ci_low": round(100 * lo, 2),
        "ci_high": round(100 * hi, 2),
        "peer_rate_pct": round(100 * x2 / n2, 2),
        "diff_pts": round(100 * diff, 2),
        "z": round(z, 1),
        "p_value": p,
    }


def add_flags(results, product, min_gap):
    m = max(len(results), 1)  # number of tests, used for the Bonferroni correction
    for r in results:
        significant = r["p_value"] < 0.05 / m
        big_enough = abs(r["diff_pts"]) >= min_gap
        r["flag"] = ("HIGHER" if r["diff_pts"] > 0 else "LOWER") if (significant and big_enough) else ""
        r["product"] = product


def run_metric(args, metric: str):
    n_sql, x_sql, label = METRICS[metric]
    name = f"{'company_report' if args.company else 'industry_outliers'}_{metric}{'_robust' if args.robust else ''}.csv"
    out_path = args.out or str(ROOT / "reports" / name)

    all_rows = []
    with sqlite3.connect(args.db) as conn:
        for product in PRODUCTS:
            counts = pd.read_sql_query(
                f"SELECT company, {n_sql} AS n, {x_sql} AS x "
                "FROM complaints WHERE product = ? GROUP BY company",
                conn, params=(product,),
            ).fillna(0)
            excluded = counts["company"].apply(lambda c: any(e in c for e in EXCLUDE))
            pool = counts[(counts["n"] >= args.min_complaints) & ~excluded]
            if pool.empty:
                print(f"[{product}] no companies meet the size cut-off, skipped")
                continue

            baseline = typical_pool(pool, args.min_gap) if args.robust else pool
            if args.company:
                targets = counts[counts["company"].str.contains(args.company.upper(), regex=False)]
            else:
                targets = pool
            if targets.empty:
                continue

            results = [r for r in (compare(row, baseline) for _, row in targets.iterrows()) if r]
            add_flags(results, product, args.min_gap)
            all_rows += results

    if not all_rows:
        print("Nothing to report. Check the company name, or lower --min-complaints.")
        return

    result = pd.DataFrame(all_rows)
    cols = ["product", "company", "complaints", "rate_pct", "ci_low", "ci_high",
            "peer_rate_pct", "diff_pts", "z", "p_value", "flag"]
    result = result[cols].sort_values(["product", "diff_pts"], ascending=[True, False])
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(out_path, index=False)

    if not args.quiet:
        pd.set_option("display.width", 220, "display.max_columns", 30, "display.max_colwidth", 38)
        show = ["company", "complaints", "rate_pct", "ci_low", "ci_high", "peer_rate_pct", "diff_pts", "flag"]
        print(f"Metric: {label}.")
        print("Baseline: " + ("typical companies only (extreme outliers removed)." if args.robust
                              else "all other companies in the peer pool.") + "\n")
        for product, grp in result.groupby("product"):
            print(f"=== {product} ===")
            if args.company or len(grp) <= 6:
                print(grp[show].to_string(index=False))
            else:
                print("Highest vs peers:")
                print(grp.head(3)[show].to_string(index=False))
                print("Lowest vs peers:")
                print(grp.tail(3)[show].to_string(index=False))
            print()
        print("Focus on the gap and its confidence interval. With this many complaints, tiny p-values are normal.")
    print(f"Saved: {out_path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(ROOT / "data" / "complaints.db"))
    ap.add_argument("--metric", choices=list(METRICS), default="relief")
    ap.add_argument("--all", action="store_true", help="Run all three metrics")
    ap.add_argument("--quiet", action="store_true", help="Only save the CSV files, skip the printed tables")
    ap.add_argument("--company", default=None,
                    help="Report on one company (text match, e.g. 'WELLS FARGO'). Omit for the industry scan.")
    ap.add_argument("--robust", action="store_true",
                    help="Use only typical companies as the baseline (ignores extreme outliers)")
    ap.add_argument("--min-complaints", type=int, default=1000,
                    help="Minimum counted complaints in a product for a company to join the peer pool")
    ap.add_argument("--min-gap", type=float, default=2.0,
                    help="Minimum gap (percentage points) before a result is flagged")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    for metric in (list(METRICS) if args.all else [args.metric]):
        run_metric(args, metric)


if __name__ == "__main__":
    main()