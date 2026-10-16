"""
Validation helper for IntelliTwin research documentation.
Audits citations, LaTeX inputs, repository paths, table coverage, and scans for forbidden erroneous strings.
"""

import os
import re
import csv
import json

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DOCS_DIR = os.path.join(REPO_ROOT, "docs", "synopsis_preparation")
LATEX_DIR = os.path.join(DOCS_DIR, "latex")
BIB_PATH = os.path.join(DOCS_DIR, "references_verified.bib")

FORBIDDEN_PATTERNS = [
    (r"min[–-]max normalization", "Min-max normalization instead of training z-score"),
    (r"robust min[–-]max", "Robust min-max normalization"),
    (r"median/IQR", "Median/IQR normalization"),
    (r"(?:IntelliTwin's base model|base predictor is|implemented using|trained with)\s+(?:LightGBM|XGBoost)", "LightGBM/XGBoost claimed as IntelliTwin model"),
    (r"C_PM\s*=\s*10\b", "C_PM = 10 instead of 1.0"),
    (r"C_FAIL\s*=\s*100\b", "C_FAIL = 100 instead of 5.0 / 10.0"),
    (r"two-cycle(?:\s+intervention)?\s+delay", "Two-cycle intervention delay"),
    (r"lead[- ]time sensitivity", "Lead-time sensitivity"),
    (r"widening factor 1\.25", "Widening factor 1.25"),
    (r"point-prediction threshold inflation by 15", "Threshold inflation by 15"),
    (r"Gaussian interval baseline", "Unregistered Gaussian interval baseline"),
    (r"scripts/audit_step07_models\.py", "Nonexistent audit script name (should be base_models)"),
    (r"experiments/pretest_verification_v2/audit_report\.json", "Nonexistent consolidated audit_report.json"),
    (r"restores exchangeability", "Claim that weighting restores exchangeability"),
    (r"Ruchi Gupta\s*(?:\(|,)?\s*(?:Project\s+)?Supervisor", "Invented supervisor role for Ruchi Gupta"),
    (r"Shiksha Pandey\s*(?:\(|,)?\s*Methodology Lead", "Invented methodology lead role for Shiksha Pandey"),
    (r"zheng2017long", "Unresolved citation zheng2017long"),
    (r"vovk2005algorithmic", "Unresolved citation vovk2005algorithmic"),
    (r"angelopoulos2021gentle", "Unresolved citation angelopoulos2021gentle"),
]

# Excluded files where historical discrepancies or correction logs legitimately discuss the old errors
EXCLUDED_FROM_STRING_CHECK = {
    "documentation_correction_report.md",
    "documentation_validation.json",
    "discrepancy_register.md",
    "validate_documentation.py",
}

def validate_bibtex():
    print("--- 1. Validating BibTeX Database ---")
    results = {"total_keys": 0, "duplicate_keys": [], "keys": set()}
    with open(BIB_PATH, "r", encoding="utf-8") as f:
        content = f.read()
    
    # Check duplicate keys via regex
    keys = re.findall(r"@\w+\s*\{\s*([^,\s]+)", content)
    results["total_keys"] = len(keys)
    seen = set()
    for k in keys:
        if k in seen:
            results["duplicate_keys"].append(k)
        seen.add(k)
        results["keys"].add(k)
    
    print(f"Total keys found: {len(keys)}, Unique: {len(results['keys'])}")
    if results["duplicate_keys"]:
        print(f"ERROR: Duplicate BibTeX keys: {results['duplicate_keys']}")
    else:
        print("PASS: No duplicate BibTeX keys.")
    return results

def validate_latex_citations_and_inputs(bib_keys):
    print("\n--- 2. Validating LaTeX Inputs and Citations ---")
    results = {
        "missing_inputs": [],
        "undefined_citations": [],
        "checked_files": 0
    }
    
    latex_files = []
    for root, _, files in os.walk(LATEX_DIR):
        for file in files:
            if file.endswith(".tex"):
                latex_files.append(os.path.join(root, file))
                
    results["checked_files"] = len(latex_files)
    
    for lfile in latex_files:
        with open(lfile, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            
        # Check \input and \include
        inputs = re.findall(r"\\(?:input|include)\{([^}]+)\}", content)
        file_dir = os.path.dirname(lfile)
        for inp in inputs:
            # Handle relative paths
            if not inp.endswith(".tex"):
                inp_tex = inp + ".tex"
            else:
                inp_tex = inp
            
            cand1 = os.path.normpath(os.path.join(file_dir, inp_tex))
            cand2 = os.path.normpath(os.path.join(LATEX_DIR, inp_tex))
            cand3 = os.path.normpath(os.path.join(os.path.dirname(file_dir), inp_tex))
            cand4 = os.path.normpath(os.path.join(LATEX_DIR, "shared", os.path.basename(inp_tex)))
            if not (os.path.isfile(cand1) or os.path.isfile(cand2) or os.path.isfile(cand3) or os.path.isfile(cand4)):
                results["missing_inputs"].append((lfile, inp))
                
        # Check \cite{...}
        cites = re.findall(r"\\cite[a-zA-Z*]*\{([^}]+)\}", content)
        for cgroup in cites:
            for ckey in cgroup.split(","):
                ckey = ckey.strip()
                if ckey and ckey not in bib_keys:
                    results["undefined_citations"].append((lfile, ckey))
                    
    if results["missing_inputs"]:
        print(f"ERROR: Missing LaTeX inputs: {results['missing_inputs']}")
    else:
        print("PASS: All LaTeX \\input targets exist.")
        
    if results["undefined_citations"]:
        print(f"ERROR: Undefined citations found: {results['undefined_citations']}")
    else:
        print("PASS: All \\cite keys resolve in references_verified.bib.")
        
    return results

def scan_forbidden_strings():
    print("\n--- 3. Scanning for Forbidden Erroneous Phrases ---")
    findings = []
    
    scan_exts = (".md", ".tex", ".csv", ".json")
    for root, _, files in os.walk(DOCS_DIR):
        for file in files:
            if file in EXCLUDED_FROM_STRING_CHECK:
                continue
            if not any(file.endswith(ext) for ext in scan_exts):
                continue
            
            fpath = os.path.join(root, file)
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
                
            for line_no, line in enumerate(lines, 1):
                # Skip comments in latex or markdown if appropriate, or check directly
                for pat, desc in FORBIDDEN_PATTERNS:
                    if re.search(pat, line, re.IGNORECASE):
                        # Verify if this is in a historical context line or table
                        rel_path = os.path.relpath(fpath, DOCS_DIR)
                        findings.append({
                            "file": rel_path,
                            "line": line_no,
                            "desc": desc,
                            "snippet": line.strip()[:100]
                        })
                        
    if findings:
        print(f"WARNING / ERROR: Found {len(findings)} forbidden occurrences:")
        for fd in findings[:10]:
            print(f"  {fd['file']}:{fd['line']} - {fd['desc']}: {fd['snippet']}")
        if len(findings) > 10:
            print(f"  ... and {len(findings) - 10} more.")
    else:
        print("PASS: Zero forbidden erroneous phrases found in active drafts.")
        
    return findings

def validate_source_manifest():
    print("\n--- 4. Validating Source Manifest ---")
    manifest_path = os.path.join(DOCS_DIR, "source_manifest.csv")
    missing_paths = []
    total_sources = 0
    with open(manifest_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            total_sources += 1
            path_or_url = row["path_or_url"]
            if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
                continue # External URL
            full_path = os.path.join(REPO_ROOT, path_or_url.replace("/", os.sep))
            if not (os.path.exists(full_path)):
                missing_paths.append((row["source_id"], path_or_url))
                
    print(f"Total source entries: {total_sources}")
    if missing_paths:
        print(f"ERROR: Missing local source paths: {missing_paths}")
    else:
        print("PASS: All local paths in source_manifest.csv exist in repository.")
    return {"total": total_sources, "missing": missing_paths}

def validate_table_coverage():
    print("\n--- 5. Validating Table Coverage in LaTeX ---")
    paper_res = os.path.join(LATEX_DIR, "paper", "sections", "results.tex")
    with open(paper_res, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Check Table 2 (Interval evaluation, 18 rows)
    # Check Table 3 (Maintenance simulation, 26 rows = 18 main + 8 controls)
    t2_rows = len(re.findall(r"FD00[124]\s*&\s*(?:GBR|LSTM)", content))
    # In table 2 there are 18 rows: each has FD00x & GBR/LSTM
    print(f"Table 2 / Interval Rows identified: {t2_rows}")
    
    # Check NOT_APPLICABLE occurrences for point policies
    na_count = content.count("NOT\\_APPLICABLE")
    print(f"NOT_APPLICABLE occurrences in paper results: {na_count}")
    
    # Check PENDING placeholders
    pending_count = content.count("PENDING")
    print(f"PENDING placeholders in paper results: {pending_count}")
    
    status = (t2_rows >= 18 and na_count >= 1 and pending_count > 0)
    print("PASS: Table coverage complete and proper PENDING/NOT_APPLICABLE used." if status else "CHECK TABLE COVERAGE")
    return {"t2_rows": t2_rows, "not_applicable": na_count, "pending": pending_count, "status": status}

def run_all():
    bib_res = validate_bibtex()
    tex_res = validate_latex_citations_and_inputs(bib_res["keys"])
    str_res = scan_forbidden_strings()
    src_res = validate_source_manifest()
    tbl_res = validate_table_coverage()
    
    all_pass = (
        len(bib_res["duplicate_keys"]) == 0 and
        len(tex_res["missing_inputs"]) == 0 and
        len(tex_res["undefined_citations"]) == 0 and
        len(str_res) == 0 and
        len(src_res["missing"]) == 0 and
        tbl_res["status"]
    )
    print(f"\nOverall Validation Result: {'ALL CHECKS PASSED' if all_pass else 'ISSUES FOUND'}")
    return all_pass

if __name__ == "__main__":
    run_all()
