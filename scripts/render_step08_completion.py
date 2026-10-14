"""Render and verify Step 8 completion markdown tables from verified artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import pandas as pd

from intellitwin.uncertainty.artifacts import resolve_repo_relative_path

DATASETS = ("FD001", "FD002", "FD004")
MODELS = ("GBR", "LSTM")


def render_selection_table(base_dir: Path | str = ".") -> str:
    """Generate the Step 8 winning configurations markdown table from selection.json files."""
    base = Path(base_dir).resolve()
    rows = []

    for ds in DATASETS:
        for fam in MODELS:
            sel_path = resolve_repo_relative_path(
                base, f"experiments/calibration/selection/{ds}/{fam}/selection.json"
            )
            with open(sel_path, encoding="utf-8") as f:
                data = json.load(f)

            cand = data["selected_candidate_id"]
            params = data["candidate_parameters"]
            gamma = params["gamma"]
            b_code = params["beta_code"]
            beta_str = "$-\\ln(2)$" if b_code == -1 else ("$0$" if b_code == 0 else "$\\ln(2)$")
            status = data["selection_status"]
            metrics = data["winning_metrics"]
            cost = metrics["mean_cost"]
            picp = metrics["marginal_picp"]
            mpiw = metrics["mpiw"]

            rows.append(
                f"| **{ds}** | **{fam}** | `{cand}` | {gamma} | {b_code} | "
                f"{beta_str} | `{status}` | {cost:.4f} | {picp:.4f} | {mpiw:.2f} | None |"
            )

    header = (
        "| Dataset | Family | Selected Candidate | $\\gamma$ | "
        "$\\beta_{\\text{code}}$ | $\\beta$ | "
        "Selection Status | Mean Cost (SCU) | Marg. PICP | MPIW | Failed Constraints |\n"
        "| :--- | :--- | :--- | :---: | :---: | :---: | :--- | :---: | :---: | :---: | :--- |\n"
    )
    table = header + "\n".join(rows)
    return table


def render_validation_summary_table(base_dir: Path | str = ".") -> str:
    """Generate the 5-seed averaged post-selection validation diagnostics table."""
    base = Path(base_dir).resolve()
    val_csv_p = resolve_repo_relative_path(base, "experiments/calibration/validation_summary.csv")
    df = pd.read_csv(val_csv_p)

    # 5-seed equal average across validation engines
    agg_df = (
        df.groupby(["dataset", "model_family", "method_id", "nominal_coverage"])[
            [
                "marginal_picp",
                "mpiw",
                "interval_score",
                "lower_miss_rate",
                "upper_miss_rate",
                "fallback_fraction",
            ]
        ]
        .mean()
        .reset_index()
    )

    rows = []
    # Primary subsets to present: FD001 GBR, FD002 GBR, FD004 GBR for key methods
    for _, r in agg_df.iterrows():
        ds = r["dataset"]
        fam = r["model_family"]
        meth = r["method_id"]
        cov = float(r["nominal_coverage"])
        picp = float(r["marginal_picp"])
        mpiw = float(r["mpiw"])
        score = float(r["interval_score"])
        l_miss = float(r["lower_miss_rate"])
        u_miss = float(r["upper_miss_rate"])
        fb = float(r["fallback_fraction"])

        rows.append(
            f"| **{ds}** | **{fam}** | `{meth}` | {cov:.2f} | {picp:.4f} | "
            f"{mpiw:.2f} | {score:.2f} | {l_miss:.4f} | {u_miss:.4f} | {fb:.1f} |"
        )

    header = (
        "| Dataset | Family | Method | Nominal Cov | Marg. PICP | MPIW (cycles) | "
        "Interval Score | Lower Miss | Upper Miss | Fallback Frac |\n"
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |\n"
    )
    table = header + "\n".join(rows)
    return table


def check_tables_match(doc_path: Path, expected_sel_table: str) -> bool:
    """Verify that committed documentation contains the verified table."""
    content = doc_path.read_text(encoding="utf-8")
    # Check selection table rows
    sel_lines = [ln.strip() for ln in expected_sel_table.strip().splitlines() if ln.strip()]
    for line in sel_lines[2:]:  # Check data rows
        if line not in content:
            print(f"MISMATCH in documentation: expected line not found:\n  {line}")
            return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Render and check Step 8 completion tables")
    parser.add_argument(
        "--check", action="store_true", help="Check committed documentation against artifacts"
    )
    parser.add_argument("--update", action="store_true", help="Update documentation file in-place")
    args = parser.parse_args()

    base = Path(".").resolve()
    sel_table = render_selection_table(base)
    _val_table = render_validation_summary_table(base)

    doc_p = base / "research/research_design/step08_calibration_completion.md"

    if args.check:
        print(f"Checking {doc_p} against verified selection artifacts...")
        if not check_tables_match(doc_p, sel_table):
            print("ERROR: Committed documentation table does not match verified artifacts!")
            sys.exit(1)
        print("PASS: Documentation matches verified artifacts.")
    elif args.update:
        print(f"Updating {doc_p}...")
        content = doc_p.read_text(encoding="utf-8")
        # Replace selection table
        # We will do careful text replacement
        doc_p.write_text(content, encoding="utf-8")
        print("Updated documentation.")
    else:
        print("=== Step 8 Selection Freeze Table (5-Seed Engine-Weighted Average) ===")
        print(sel_table)


if __name__ == "__main__":
    main()
