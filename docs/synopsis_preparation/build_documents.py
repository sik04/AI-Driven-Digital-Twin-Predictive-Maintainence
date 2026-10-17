"""
Build script for IntelliTwin research documentation deliverables.

Compiles the four LaTeX deliverables (hypotheses appendix, research synopsis,
IEEE paper draft, and academic thesis draft) into isolated temporary directories
using Tectonic or latexmk, copies the resulting PDFs to the previews directory,
and generates a cryptographic build manifest.
"""

from __future__ import annotations

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

import pypdf

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS_DIR = REPO_ROOT / "docs" / "synopsis_preparation"
LATEX_DIR = DOCS_DIR / "latex"
PREVIEWS_DIR = DOCS_DIR / "previews"
MANIFEST_PATH = DOCS_DIR / "build_manifest.json"

DOCUMENTS = {
    "hypotheses_appendix": {
        "source_rel": "docs/synopsis_preparation/latex/hypotheses/main.tex",
        "output_pdf_name": "hypotheses_appendix.pdf",
        "work_dir": LATEX_DIR / "hypotheses",
    },
    "synopsis_draft": {
        "source_rel": "docs/synopsis_preparation/latex/synopsis/main.tex",
        "output_pdf_name": "synopsis_draft.pdf",
        "work_dir": LATEX_DIR / "synopsis",
    },
    "ieee_paper_draft": {
        "source_rel": "docs/synopsis_preparation/latex/paper/main.tex",
        "output_pdf_name": "ieee_paper_draft.pdf",
        "work_dir": LATEX_DIR / "paper",
    },
    "thesis_draft": {
        "source_rel": "docs/synopsis_preparation/latex/thesis/main.tex",
        "output_pdf_name": "thesis_draft.pdf",
        "work_dir": LATEX_DIR / "thesis",
    },
}


def compute_sha256(filepath: Path) -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


def get_git_commit() -> str:
    """Get the current HEAD commit hash."""
    try:
        res = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=True,
        )
        return res.stdout.strip()
    except Exception:
        return "UNKNOWN_COMMIT"


def collect_source_hashes() -> dict[str, str]:
    """Collect SHA-256 hashes for all LaTeX source files and verified bibliography."""
    hashes: dict[str, str] = {}

    bib_file = DOCS_DIR / "references_verified.bib"
    if bib_file.is_file():
        rel = bib_file.relative_to(REPO_ROOT).as_posix()
        hashes[rel] = compute_sha256(bib_file)

    for ext in ("*.tex", "*.bib", "*.cls", "*.sty"):
        for path in LATEX_DIR.rglob(ext):
            if path.is_file():
                rel = path.relative_to(REPO_ROOT).as_posix()
                hashes[rel] = compute_sha256(path)

    return dict(sorted(hashes.items()))


def get_page_count(pdf_path: Path) -> int:
    """Count pages in a generated PDF using pypdf."""
    try:
        reader = pypdf.PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as e:
        print(f"Warning: could not read page count from {pdf_path}: {e}")
        return -1


def check_warnings(log_output: str) -> tuple[list[str], list[str]]:
    """Inspect compilation log for undefined citations and references."""
    citation_warnings: list[str] = []
    reference_warnings: list[str] = []

    for line in log_output.splitlines():
        if re.search(r"citation .* undefined", line, re.IGNORECASE):
            citation_warnings.append(line.strip())
        elif re.search(r"reference .* undefined", line, re.IGNORECASE):
            reference_warnings.append(line.strip())

    return citation_warnings, reference_warnings


def detect_compiler(preferred: str = "auto") -> tuple[str, str]:
    """Locate compiler executable and version."""
    if preferred == "latexmk" or (preferred == "auto" and shutil.which("latexmk")):
        latexmk_bin = shutil.which("latexmk")
        if latexmk_bin:
            try:
                res = subprocess.run(
                    [latexmk_bin, "-v"],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                ver_line = res.stdout.splitlines()[0] if res.stdout else "latexmk"
                return latexmk_bin, ver_line.strip()
            except Exception:
                pass

    tectonic_bin = shutil.which("tectonic")
    if not tectonic_bin:
        # Fallback check common locations
        user_home = Path(os.environ.get("USERPROFILE", ""))
        user_bin = user_home / ".gemini" / "antigravity-ide" / "bin" / "tectonic.exe"
        if user_bin.is_file():
            tectonic_bin = str(user_bin)

    if tectonic_bin:
        try:
            res = subprocess.run(
                [tectonic_bin, "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            ver = res.stdout.strip() or res.stderr.strip() or "Tectonic"
            return tectonic_bin, ver
        except Exception:
            pass

    raise RuntimeError("No supported LaTeX compiler found. Please install Tectonic or Latexmk.")


def build_all(compiler_pref: str = "auto") -> bool:
    """Build all four LaTeX deliverables and generate build manifest."""
    PREVIEWS_DIR.mkdir(parents=True, exist_ok=True)
    compiler_bin, compiler_ver = detect_compiler(compiler_pref)
    is_tectonic = "tectonic" in Path(compiler_bin).name.lower()

    print(f"Using LaTeX compiler: {compiler_bin} ({compiler_ver})")
    print(f"Repository commit: {get_git_commit()}")

    source_hashes = collect_source_hashes()
    manifest_docs: dict[str, Any] = {}
    all_success = True

    import tempfile

    for doc_id, doc_info in DOCUMENTS.items():
        print("\n==========================================")
        print(f"Building {doc_id}...")
        print(f"Source: {doc_info['source_rel']}")

        with tempfile.TemporaryDirectory() as tmp_out:
            work_dir = doc_info["work_dir"]
            main_tex = work_dir / "main.tex"
            if not main_tex.is_file():
                print(f"ERROR: Entry point {main_tex} does not exist.")
                all_success = False
                continue

            if is_tectonic:
                cmd = [compiler_bin, "-o", tmp_out, str(main_tex)]
            else:
                cmd = [
                    compiler_bin,
                    "-pdf",
                    "-interaction=nonstopmode",
                    f"-outdir={tmp_out}",
                    "main.tex",
                ]

            cmd_str = " ".join(cmd)
            print(f"Command: {cmd_str}")

            proc = subprocess.run(
                cmd,
                cwd=str(work_dir),
                capture_output=True,
                text=True,
            )

            log_output = proc.stdout + "\n" + proc.stderr
            citation_warns, ref_warns = check_warnings(log_output)

            pdf_tmp = Path(tmp_out) / "main.pdf"
            exit_code = proc.returncode
            target_pdf_rel = f"docs/synopsis_preparation/previews/{doc_info['output_pdf_name']}"

            if exit_code != 0 or not pdf_tmp.is_file():
                print(f"ERROR: Build failed for {doc_id} (exit code {exit_code}).")
                print(proc.stderr[:1000])
                all_success = False
                manifest_docs[doc_id] = {
                    "entry_point": doc_info["source_rel"],
                    "target_pdf": target_pdf_rel,
                    "command": cmd_str,
                    "exit_code": exit_code,
                    "pdf_sha256": None,
                    "page_count": None,
                    "citation_warning_status": citation_warns or "NONE",
                    "reference_warning_status": ref_warns or "NONE",
                    "status": "FAILED",
                }
                continue

            # Move PDF to previews directory
            final_pdf = PREVIEWS_DIR / doc_info["output_pdf_name"]
            shutil.copy2(pdf_tmp, final_pdf)
            pdf_hash = compute_sha256(final_pdf)
            page_count = get_page_count(final_pdf)

            print(f"SUCCESS: Generated {final_pdf.name}")
            print(f"  Pages: {page_count}, SHA-256: {pdf_hash[:16]}...")
            if citation_warns:
                print(f"  WARNING: {len(citation_warns)} citation warning(s)")
            if ref_warns:
                print(f"  WARNING: {len(ref_warns)} reference warning(s)")

            manifest_docs[doc_id] = {
                "entry_point": doc_info["source_rel"],
                "target_pdf": target_pdf_rel,
                "command": cmd_str,
                "exit_code": exit_code,
                "pdf_sha256": pdf_hash,
                "page_count": page_count,
                "citation_warning_status": citation_warns if citation_warns else "NONE",
                "reference_warning_status": ref_warns if ref_warns else "NONE",
                "status": "SUCCESS",
            }

    # Write build manifest (without self-referential hash)
    manifest_data = {
        "source_commit": get_git_commit(),
        "generated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "compiler": compiler_bin,
        "compiler_version": compiler_ver,
        "overall_status": "SUCCESS" if all_success else "FAILED",
        "documents": manifest_docs,
        "source_files": source_hashes,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    print(f"\nWrote build manifest: {MANIFEST_PATH.relative_to(REPO_ROOT).as_posix()}")
    print(f"Build result: {'ALL FOUR DELIVERABLES COMPILED' if all_success else 'BUILD FAILED'}")

    return all_success


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile IntelliTwin research documentation deliverables."
    )
    parser.add_argument(
        "--compiler",
        choices=["auto", "tectonic", "latexmk"],
        default="auto",
        help="Preferred LaTeX compiler pipeline (default: auto)",
    )
    args = parser.parse_args()

    success = build_all(compiler_pref=args.compiler)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
