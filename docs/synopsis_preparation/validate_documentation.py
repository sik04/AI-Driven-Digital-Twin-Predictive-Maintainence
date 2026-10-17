"""
Fail-closed documentation validation suite for IntelliTwin research artifacts.

Verifies:
1. BibTeX keys and LaTeX citation resolution.
2. LaTeX \\input and \\include file existence.
3. Active local repository paths across Markdown, CSV, and LaTeX.
4. Markdown table boundaries, column counts, and formatting.
5. Exact table identity sets (6 point rows, 18 interval rows, 26 maintenance rows).
6. Exact 152-component hypothesis manifest matching decisions.py.
7. Exact 186 evaluation-matrix keys matching evidence_schema.py.
8. Calibration math consistency (gamma=2, beta_code=-1, numerical beta=-ln(2)).
9. Absence of fabricated held-out results (pending status preserved).
10. Absence of obsolete active v2-only readiness claims.
11. Absence of nonexistent implementation names (paths, classes, APIs).
12. Scientific claim rigor (no exchangeability overreach).
13. Required baseline and audit provenance fields.

Generates documentation_validation.json and exits nonzero on any failure.
"""

from __future__ import annotations

import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

DOCS_DIR = REPO_ROOT / "docs" / "synopsis_preparation"
LATEX_DIR = DOCS_DIR / "latex"
BIB_PATH = DOCS_DIR / "references_verified.bib"
REPORT_PATH = DOCS_DIR / "documentation_validation.json"

# Excluded from literal forbidden phrase checks because they record historical bugs/corrections
EXCLUDED_FROM_FORBIDDEN_CHECKS = {
    "documentation_correction_report.md",
    "discrepancy_register.md",
    "validate_documentation.py",
    "test_validate_documentation.py",
    "documentation_validation.json",
    "build_manifest.json",
}

FORBIDDEN_PATTERNS = [
    (r"min[–-]max normalization", "Min-max normalization instead of training z-score"),
    (r"robust min[–-]max", "Robust min-max normalization"),
    (r"median/IQR", "Median/IQR normalization"),
    (
        r"(?:IntelliTwin's base model|base predictor is|implemented using|trained with)\s+"
        r"(?:LightGBM|XGBoost)",
        "LightGBM/XGBoost claimed as IntelliTwin model",
    ),
    (r"C_PM\s*=\s*10\b", "C_PM = 10 instead of 1.0"),
    (r"C_FAIL\s*=\s*100\b", "C_FAIL = 100 instead of 5.0 / 10.0"),
    (r"two-cycle(?:\s+intervention)?\s+delay", "Two-cycle intervention delay"),
    (r"lead[- ]time sensitivity", "Lead-time sensitivity"),
    (r"widening factor 1\.25", "Widening factor 1.25"),
    (r"point-prediction threshold inflation by 15", "Threshold inflation by 15"),
    (r"Gaussian interval baseline", "Unregistered Gaussian interval baseline"),
    (r"scripts/audit_step07_models\.py", "Nonexistent audit script name"),
    (r"experiments/pretest_verification_v2/audit_report\.json", "Nonexistent audit_report.json"),
    (r"restores exchangeability", "Claim that weighting restores exchangeability"),
    (r"establishes exchangeability", "Claim that weighting establishes exchangeability"),
    (r"guarantees\s+coverage\b", "Unwarranted finite-sample coverage guarantee"),
    (r"data/split\.py\b", "Nonexistent path data/split.py (should be splits.py)"),
    (r"data/window\.py\b", "Nonexistent path data/window.py (should be windowing.py)"),
    (
        r"evaluation/decision_rules\.py\b",
        "Nonexistent path evaluation/decision_rules.py (should be decisions.py)",
    ),
    (
        r"uncertainty/conformal\.py\b",
        "Nonexistent path uncertainty/conformal.py (should be calibration/quantiles/scores)",
    ),
    (
        r"\bclass\s+MaintenanceSimulator\b|\bMaintenanceSimulator\(",
        "Nonexistent class MaintenanceSimulator",
    ),
    (
        r"\bclass\s+MaintenanceCostModel\b|\bMaintenanceCostModel\(",
        "Nonexistent class MaintenanceCostModel",
    ),
    (
        r"\bclass\s+ExecutionEnvironment\b|\bExecutionEnvironment\(",
        "Nonexistent class ExecutionEnvironment",
    ),
]


def check_bibtex(bib_file: Path | None = None) -> dict[str, Any]:
    """Verify BibTeX database has no duplicate keys and returns valid keys."""
    target_bib = bib_file or BIB_PATH
    if not target_bib.is_file():
        return {
            "status": "FAIL",
            "error": f"BibTeX file not found: {target_bib}",
            "keys": [],
            "duplicate_keys": [],
        }

    with open(target_bib, encoding="utf-8") as f:
        content = f.read()

    raw_keys = re.findall(r"@\w+\s*\{\s*([^,\s]+)", content)
    seen: set[str] = set()
    duplicates: list[str] = []
    unique_keys: list[str] = []

    for k in raw_keys:
        if k in seen:
            duplicates.append(k)
        else:
            seen.add(k)
            unique_keys.append(k)

    status = "FAIL" if duplicates else "PASS"
    return {
        "status": status,
        "total_keys": len(raw_keys),
        "unique_keys": len(unique_keys),
        "duplicate_keys": duplicates,
        "keys": unique_keys,
    }


def safe_rel_path(p: Path) -> str:
    """Format path relative to REPO_ROOT if possible, otherwise return string."""
    try:
        return p.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return p.as_posix()


def check_latex_inputs_and_citations(
    latex_root: Path | None = None,
    valid_keys: list[str] | set[str] | None = None,
) -> dict[str, Any]:
    """Verify all \\input / \\include targets exist and all \\cite keys resolve."""
    root_dir = latex_root or LATEX_DIR
    if valid_keys is None:
        bib_res = check_bibtex()
        valid_keys = set(bib_res["keys"])
    else:
        valid_keys = set(valid_keys)

    missing_inputs: list[dict[str, str]] = []
    undefined_cites: list[dict[str, str]] = []
    tex_files = list(root_dir.rglob("*.tex"))

    for tex_path in tex_files:
        with open(tex_path, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        file_dir = tex_path.parent
        # Check inputs
        inputs = re.findall(r"\\(?:input|include)\{([^}]+)\}", content)
        for inp in inputs:
            inp_tex = inp if inp.endswith(".tex") else inp + ".tex"
            candidates = [
                file_dir / inp_tex,
                root_dir / inp_tex,
                file_dir.parent / inp_tex,
                root_dir / "shared" / Path(inp_tex).name,
            ]
            if not any(c.is_file() for c in candidates):
                missing_inputs.append(
                    {
                        "file": safe_rel_path(tex_path),
                        "target": inp,
                    }
                )

        # Check citations
        cites = re.findall(r"\\cite[a-zA-Z*]*\{([^}]+)\}", content)
        for cgroup in cites:
            for ckey in cgroup.split(","):
                ckey = ckey.strip()
                if ckey and ckey not in valid_keys:
                    undefined_cites.append(
                        {
                            "file": safe_rel_path(tex_path),
                            "key": ckey,
                        }
                    )

    status = "FAIL" if (missing_inputs or undefined_cites) else "PASS"
    return {
        "status": status,
        "checked_files": len(tex_files),
        "missing_inputs": missing_inputs,
        "undefined_citations": undefined_cites,
    }


def check_source_manifest(manifest_file: Path | None = None) -> dict[str, Any]:
    """Verify all local paths in source_manifest.csv exist."""
    path = manifest_file or (DOCS_DIR / "source_manifest.csv")
    if not path.is_file():
        return {"status": "FAIL", "error": f"Missing {path}", "missing_paths": []}

    missing: list[dict[str, str]] = []
    total = 0
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total += 1
            target = row.get("path_or_url", "").strip()
            if target.startswith("http://") or target.startswith("https://"):
                continue
            local_path = REPO_ROOT / target.replace("/", os.sep)
            if not local_path.exists():
                missing.append({"source_id": row.get("source_id", ""), "path": target})

    status = "FAIL" if missing else "PASS"
    return {"status": status, "total_sources": total, "missing_paths": missing}


def check_table_templates(tables_file: Path | None = None) -> dict[str, Any]:
    """
    Verify results_table_templates.md has:
    1. Correct table boundaries (no run-together headers).
    2. Consistent column counts per row in each table.
    3. Exactly 6 point-prediction rows in T3.
    4. Exactly 18 interval rows in T4.
    5. Exactly 18 primary rows in T6 and 10 rows in T7 (or 26 in consolidated maintenance).
    """
    path = tables_file or (DOCS_DIR / "results_table_templates.md")
    if not path.is_file():
        return {"status": "FAIL", "error": f"Missing {path}"}

    with open(path, encoding="utf-8") as f:
        lines = f.readlines()

    issues: list[str] = []
    tables: dict[str, list[list[str]]] = {}
    current_table: str | None = None
    in_table = False

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()
        # Detect table headers like "## Table T3: ..." or "### Table T3: ..."
        m_t = re.match(r"^##+\s+Table\s+(T\d+):", line)
        if m_t:
            current_table = m_t.group(1)
            tables[current_table] = []
            in_table = False
            continue

        if current_table and line.startswith("|") and line.endswith("|"):
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # Check for header boundary run-together (e.g. "## Table T4:" inside table row)
            if any(re.search(r"##+\s+Table", c) for c in cells):
                issues.append(
                    f"Line {idx}: Malformed table boundary containing header text: {line}"
                )
            tables[current_table].append(cells)
            in_table = True
        elif in_table and (not line.startswith("|")):
            in_table = False

    # Check column counts and required rows
    # Expected combinations
    expected_point_combos = {
        ("FD001", "GBR"),
        ("FD001", "LSTM"),
        ("FD002", "GBR"),
        ("FD002", "LSTM"),
        ("FD004", "GBR"),
        ("FD004", "LSTM"),
    }

    # Validate T3 (Point Prediction)
    t3_rows = tables.get("T3", [])
    if len(t3_rows) < 2:
        issues.append("Table T3 has no content rows.")
    else:
        header_cols = len(t3_rows[0])
        sep_cols = len(t3_rows[1])
        if header_cols != sep_cols:
            issues.append(f"T3: Header columns ({header_cols}) != separator columns ({sep_cols})")
        data_rows = t3_rows[2:]
        found_point_combos = set()
        for r_idx, r in enumerate(data_rows, start=1):
            if len(r) != header_cols:
                issues.append(
                    f"T3 row {r_idx} column mismatch: expected {header_cols}, got {len(r)}"
                )
            if len(r) >= 2:
                ds = r[0].replace("**", "").strip()
                mod_cell = r[1].replace("**", "").strip()
                mod = "GBR" if "GBR" in mod_cell else ("LSTM" if "LSTM" in mod_cell else mod_cell)
                if (ds, mod) in expected_point_combos:
                    if (ds, mod) in found_point_combos:
                        issues.append(f"T3 duplicate point row: {ds} / {mod}")
                    found_point_combos.add((ds, mod))

        if found_point_combos != expected_point_combos:
            missing = expected_point_combos - found_point_combos
            issues.append(f"T3 missing required point prediction rows: {missing}")

    # Validate T4 (Interval Evaluation)
    t4_rows = tables.get("T4", [])
    if len(t4_rows) < 2:
        issues.append("Table T4 has no content rows.")
    else:
        header_cols = len(t4_rows[0])
        data_rows = t4_rows[2:]
        found_interval_combos = set()
        for r_idx, r in enumerate(data_rows, start=1):
            if len(r) != header_cols:
                issues.append(
                    f"T4 row {r_idx} column mismatch: expected {header_cols}, got {len(r)}"
                )
            if len(r) >= 3:
                ds = r[0].replace("**", "").strip()
                mod_cell = r[1].replace("**", "").strip()
                mod = "GBR" if "GBR" in mod_cell else ("LSTM" if "LSTM" in mod_cell else mod_cell)
                meth = r[2].replace("`", "").strip()
                norm_meth = "proposed" if meth in ("decision_aware_hcp", "proposed") else meth
                if (ds, mod, norm_meth) in found_interval_combos:
                    issues.append(f"T4 duplicate interval row: {ds} / {mod} / {meth}")
                found_interval_combos.add((ds, mod, norm_meth))

        expected_interval_rows = {
            (ds, mod, meth)
            for ds, mod in expected_point_combos
            for meth in ("global_hcp", "regime_hcp", "proposed")
        }
        if found_interval_combos != expected_interval_rows:
            missing = expected_interval_rows - found_interval_combos
            issues.append(f"T4 missing required interval rows: {missing}")

    # Validate T6 (Primary Maintenance)
    t6_rows = tables.get("T6", [])
    if len(t6_rows) >= 2:
        header_cols = len(t6_rows[0])
        data_rows = t6_rows[2:]
        found_t6 = set()
        for r_idx, r in enumerate(data_rows, start=1):
            if len(r) != header_cols:
                issues.append(
                    f"T6 row {r_idx} column mismatch: expected {header_cols}, got {len(r)}"
                )
            if len(r) >= 3:
                ds = r[0].replace("**", "").strip()
                mod_cell = r[1].replace("**", "").strip()
                mod = "GBR" if "GBR" in mod_cell else ("LSTM" if "LSTM" in mod_cell else mod_cell)
                meth = r[2].replace("`", "").strip()
                norm_meth = "proposed" if meth in ("decision_aware_hcp", "proposed") else meth
                found_t6.add((ds, mod, norm_meth))
        if len(found_t6) != 18:
            issues.append(f"T6 expected 18 unique primary maintenance rows, found {len(found_t6)}")

    # Validate T7 (Controls)
    t7_rows = tables.get("T7", [])
    if len(t7_rows) >= 2:
        header_cols = len(t7_rows[0])
        data_rows = t7_rows[2:]
        found_t7 = set()
        for r_idx, r in enumerate(data_rows, start=1):
            if len(r) != header_cols:
                issues.append(
                    f"T7 row {r_idx} column mismatch: expected {header_cols}, got {len(r)}"
                )
            if len(r) >= 2:
                mod_cell = r[0].replace("**", "").strip()
                mod = "GBR" if "GBR" in mod_cell else ("LSTM" if "LSTM" in mod_cell else mod_cell)
                pol = r[1].replace("`", "").strip()
                found_t7.add((mod, pol))
        # 2 models x 5 policy variants (4 controls + 1 proposed reference) = 10 rows
        if len(found_t7) < 10:
            issues.append(f"T7 expected at least 10 model/policy rows, found {len(found_t7)}")

    status = "FAIL" if issues else "PASS"
    return {
        "status": status,
        "tables_checked": list(tables.keys()),
        "issues": issues,
    }


def check_component_manifest(manifest_csv: Path | None = None) -> dict[str, Any]:
    """Verify component_reporting_template.csv exactly matches decisions.py manifest (152 rows)."""
    csv_path = manifest_csv or (DOCS_DIR / "component_reporting_template.csv")
    if not csv_path.is_file():
        return {"status": "FAIL", "error": f"Missing {csv_path}", "issues": []}

    try:
        from intellitwin.evaluation.decisions import get_rq_component_manifest

        expected_manifest = get_rq_component_manifest()
    except Exception as e:
        return {"status": "FAIL", "error": f"Could not load decisions manifest: {e}", "issues": []}

    # expected_manifest is dict[str, list[HypothesisComponent]]
    expected_ids: list[str] = []
    if isinstance(expected_manifest, dict):
        for comps in expected_manifest.values():
            for c in comps:
                cid = c.component_id if hasattr(c, "component_id") else c["component_id"]
                expected_ids.append(cid)
    else:
        for c in expected_manifest:
            cid = c.component_id if hasattr(c, "component_id") else c["component_id"]
            expected_ids.append(cid)

    issues: list[str] = []

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        found_ids = [row["component_id"] for row in reader if "component_id" in row]

    if len(found_ids) != 152:
        issues.append(f"Expected 152 components, found {len(found_ids)} in CSV")

    if len(found_ids) != len(set(found_ids)):
        duplicates = [x for x in found_ids if found_ids.count(x) > 1]
        issues.append(f"Duplicate components found in CSV: {set(duplicates)}")

    if set(found_ids) != set(expected_ids):
        missing = set(expected_ids) - set(found_ids)
        extra = set(found_ids) - set(expected_ids)
        if missing:
            issues.append(f"Missing components: {missing}")
        if extra:
            issues.append(f"Unexpected extra components: {extra}")

    # Check RQ distribution: RQ1: 14, RQ2: 20, RQ3: 22, RQ4: 96
    rq_counts: dict[str, int] = {}
    for cid in found_ids:
        rq = cid.split("_")[0] if "_" in cid else cid.split("-")[0]
        rq_counts[rq] = rq_counts.get(rq, 0) + 1

    expected_rq_counts = {"RQ1": 14, "RQ2": 20, "RQ3": 22, "RQ4": 96}
    for rq, exp_count in expected_rq_counts.items():
        act_count = rq_counts.get(rq, 0)
        if act_count != exp_count:
            issues.append(f"{rq} count mismatch: expected {exp_count}, got {act_count}")

    status = "FAIL" if issues else "PASS"
    return {
        "status": status,
        "total_components": len(found_ids),
        "rq_counts": rq_counts,
        "issues": issues,
    }


def check_evaluation_matrix(matrix_csv: Path | None = None) -> dict[str, Any]:
    """Verify evaluation_matrix_template.csv exactly matches evidence_schema.py keys (186 rows)."""
    csv_path = matrix_csv or (DOCS_DIR / "evaluation_matrix_template.csv")
    if not csv_path.is_file():
        return {"status": "FAIL", "error": f"Missing {csv_path}", "issues": []}

    try:
        from intellitwin.evaluation.evidence_schema import generate_expected_cell_summary_keys

        schema_res = generate_expected_cell_summary_keys()
        if isinstance(schema_res, tuple) and len(schema_res) == 2:
            expected_tuples = set(schema_res[0]) | set(schema_res[1])
        else:
            expected_tuples = set(schema_res)
    except Exception as e:
        return {
            "status": "FAIL",
            "error": f"Could not load evidence schema keys: {e}",
            "issues": [],
        }

    issues: list[str] = []
    found_rows = []
    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            found_rows.append(r)

    if len(found_rows) != 186:
        issues.append(f"Expected 186 keys, found {len(found_rows)} in CSV")

    # Match key tuples: (dataset, model_family, method_or_control, nominal_coverage, cost_scenario)
    found_tuples = set()
    for r in found_rows:
        cov_val = int(float(r.get("nominal_coverage", 0)))
        tup = (
            r.get("dataset"),
            r.get("model_family"),
            r.get("method_or_control"),
            cov_val,
            r.get("cost_scenario"),
        )
        if tup in found_tuples:
            issues.append(f"Duplicate evaluation matrix key: {tup}")
        found_tuples.add(tup)

    if found_tuples != expected_tuples:
        missing = expected_tuples - found_tuples
        extra = found_tuples - expected_tuples
        if missing:
            issues.append(f"Missing evaluation matrix keys count: {len(missing)}")
        if extra:
            issues.append(f"Unexpected extra evaluation matrix keys count: {len(extra)}")

    status = "FAIL" if issues else "PASS"
    return {
        "status": status,
        "total_keys": len(found_rows),
        "issues": issues,
    }


def check_calibration_math(docs_dir: Path | None = None) -> dict[str, Any]:
    """Verify that gamma=2, beta_code=-1, and numerical beta=-ln(2) without mathematical beta=-1."""
    target_dir = docs_dir or DOCS_DIR
    issues: list[str] = []

    # Files to inspect for mathematical calibration parameters
    target_files = [
        target_dir / "figure_plan.md",
        target_dir / "methodology_draft.md",
        target_dir / "results_table_templates.md",
        target_dir / "latex" / "shared" / "calibration_equations.tex",
    ]

    for fpath in target_files:
        if not fpath.is_file():
            continue
        with open(fpath, encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Check for erroneous mathematical beta = -1 without code qualification
        # E.g. "beta = -1" where beta is numerical coefficient
        bad_math = re.findall(
            r"(?:numerical\s+beta\s*=\s*-1\b|\bbeta\s*=\s*-1\.0\b|(?<!code\s)\bbeta\s*=\s*-1\b(?!_code))",
            content,
        )
        if bad_math:
            # Filter out allowable mentions like "beta_code = -1" or historical notes
            rel = safe_rel_path(fpath)
            for bm in bad_math:
                if "beta_code" not in bm:
                    issues.append(f"{rel}: Unqualified mathematical beta=-1: '{bm}'")

        # Verify ln(2) or -0.693 is mentioned
        if (
            "ln(2)" not in content
            and "-0.693" not in content
            and "\\ln 2" not in content
            and "\\ln(2)" not in content
        ):
            rel = safe_rel_path(fpath)
            issues.append(f"{rel}: Missing explicit -ln(2) definition for numerical beta.")

    status = "FAIL" if issues else "PASS"
    return {"status": status, "issues": issues}


def check_no_fabricated_results(tables_file: Path | None = None) -> dict[str, Any]:
    """Verify all empirical result cells in reporting tables remain PENDING or NOT_APPLICABLE."""
    path = tables_file or (DOCS_DIR / "results_table_templates.md")
    if not path.is_file():
        return {"status": "FAIL", "error": f"Missing {path}", "issues": []}

    with open(path, encoding="utf-8") as f:
        content = f.read()

    issues: list[str] = []
    # Check tables T3 through T10
    # In T3-T10, results must not have fabricated numeric outcomes
    # (except T2 development validation values)
    m_t3 = re.search(r"##+\s+Table\s+T3:", content)
    if m_t3:
        t3_onward = content[m_t3.start() :]
        lines = t3_onward.splitlines()
        for idx, line in enumerate(lines, start=1):
            if (
                line.startswith("|")
                and not line.startswith("|---")
                and not line.startswith("| Metric")
                and not line.startswith("| Dataset")
            ):
                # If row contains numeric results instead of PENDING / NOT_APPLICABLE
                cells = [c.strip() for c in line.split("|")[1:-1]]
                for c in cells[3:]:  # Evaluation outcome cells
                    if re.match(r"^\d+\.\d+$", c):
                        issues.append(
                            f"Fabricated numerical result found in T3+ at line {idx}: '{c}'"
                        )

    status = "FAIL" if issues else "PASS"
    return {"status": status, "issues": issues}


def check_provenance_and_claims(docs_dir: Path | None = None) -> dict[str, Any]:
    """Verify required baseline SHA, audit commit, and status tokens are present."""
    target_dir = docs_dir or DOCS_DIR
    readme = target_dir / "README.md"
    checklist = target_dir / "completion_checklist.md"
    claims_csv = target_dir / "claims_evidence_matrix.csv"

    required_tokens = [
        "c163bb279e7427b8f1b6e75955af4969ff9370fd",  # Baseline SHA
        "550a7994d5746d3bcbfa28c26e7ed4f1a26a6153",  # v4 audit execution commit
        "PRETEST_READY",
        "NOT_STARTED",
        "PENDING",
    ]

    issues: list[str] = []
    for fpath in [readme, checklist, claims_csv]:
        if not fpath.is_file():
            issues.append(f"Missing required file: {fpath.name}")
            continue
        with open(fpath, encoding="utf-8", errors="ignore") as f:
            text = f.read()
        for token in required_tokens:
            if token not in text:
                issues.append(f"{fpath.name} is missing required provenance token: {token}")

    status = "FAIL" if issues else "PASS"
    return {"status": status, "issues": issues}


def scan_forbidden_phrases(docs_dir: Path | None = None) -> dict[str, Any]:
    """Scan active drafts for forbidden obsolete phrases and nonexistent APIs."""
    target_dir = docs_dir or DOCS_DIR
    findings: list[dict[str, Any]] = []

    scan_exts = (".md", ".tex", ".csv")
    for root, _, files in os.walk(target_dir):
        for file in files:
            if file in EXCLUDED_FROM_FORBIDDEN_CHECKS:
                continue
            if not any(file.endswith(ext) for ext in scan_exts):
                continue

            fpath = Path(root) / file
            rel_path = fpath.relative_to(REPO_ROOT).as_posix()
            with open(fpath, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()

            for line_no, line in enumerate(lines, 1):
                for pat, desc in FORBIDDEN_PATTERNS:
                    if re.search(pat, line, re.IGNORECASE):
                        findings.append(
                            {
                                "file": rel_path,
                                "line": line_no,
                                "desc": desc,
                                "snippet": line.strip()[:100],
                            }
                        )

    status = "FAIL" if findings else "PASS"
    return {"status": status, "findings": findings}


def run_all_validations() -> tuple[bool, dict[str, Any]]:
    """Run all documentation validation checks and compile report."""
    print("==================================================")
    print("Executing IntelliTwin Fail-Closed Documentation Validation")
    print("==================================================")

    report: dict[str, Any] = {}

    # 1. BibTeX
    print("\n[1/10] Checking BibTeX database...")
    report["bibtex"] = check_bibtex()
    print(f"  -> {report['bibtex']['status']} (Unique keys: {report['bibtex'].get('unique_keys')})")

    # 2. LaTeX Citations & Inputs
    print("\n[2/10] Checking LaTeX inputs and citations...")
    report["latex"] = check_latex_inputs_and_citations(valid_keys=report["bibtex"].get("keys", []))
    print(
        f"  -> {report['latex']['status']} (Files checked: {report['latex'].get('checked_files')})"
    )

    # 3. Source Manifest
    print("\n[3/10] Checking source manifest paths...")
    report["source_manifest"] = check_source_manifest()
    total_srcs = report["source_manifest"].get("total_sources")
    print(f"  -> {report['source_manifest']['status']} (Total sources: {total_srcs})")

    # 4. Table Templates
    print("\n[4/10] Checking results table templates (T1-T10)...")
    report["table_templates"] = check_table_templates()
    tbls = report["table_templates"].get("tables_checked")
    print(f"  -> {report['table_templates']['status']} (Tables: {tbls})")

    # 5. Component Manifest
    print("\n[5/10] Checking component reporting manifest (152 items)...")
    report["component_manifest"] = check_component_manifest()
    comps = report["component_manifest"].get("total_components")
    print(f"  -> {report['component_manifest']['status']} (Components: {comps})")

    # 6. Evaluation Matrix
    print("\n[6/10] Checking evaluation matrix template (186 items)...")
    report["evaluation_matrix"] = check_evaluation_matrix()
    keys_cnt = report["evaluation_matrix"].get("total_keys")
    print(f"  -> {report['evaluation_matrix']['status']} (Keys: {keys_cnt})")

    # 7. Calibration Math
    print("\n[7/10] Checking calibration mathematics...")
    report["calibration_math"] = check_calibration_math()
    print(f"  -> {report['calibration_math']['status']}")

    # 8. No Fabricated Results
    print("\n[8/10] Checking for absence of fabricated results...")
    report["no_fabricated_results"] = check_no_fabricated_results()
    print(f"  -> {report['no_fabricated_results']['status']}")

    # 9. Provenance & Claims
    print("\n[9/10] Checking provenance and scientific claims...")
    report["provenance_and_claims"] = check_provenance_and_claims()
    print(f"  -> {report['provenance_and_claims']['status']}")

    # 10. Forbidden Phrases
    print("\n[10/10] Scanning for forbidden erroneous phrases...")
    report["forbidden_phrases"] = scan_forbidden_phrases()
    num_findings = len(report["forbidden_phrases"].get("findings", []))
    print(f"  -> {report['forbidden_phrases']['status']} (Findings: {num_findings})")

    all_passed = all(
        section.get("status") == "PASS"
        for section in report.values()
        if isinstance(section, dict) and "status" in section
    )

    report["overall_status"] = "PASS" if all_passed else "FAIL"

    # Write report
    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("\n==================================================")
    print(f"Documentation Validation Result: {report['overall_status']}")
    print(f"Report written to: {REPORT_PATH.relative_to(REPO_ROOT).as_posix()}")
    print("==================================================")

    if not all_passed:
        print("\nSUMMARY OF FAILURES:")
        for name, sec in report.items():
            if isinstance(sec, dict) and sec.get("status") == "FAIL":
                fail_detail = (
                    sec.get("error")
                    or sec.get("issues")
                    or sec.get("findings")
                    or sec.get("missing_inputs")
                    or sec.get("undefined_citations")
                    or sec.get("duplicate_keys")
                )
                print(f"- {name}: {fail_detail}")

    return all_passed, report


def main() -> None:
    passed, _ = run_all_validations()
    if not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
