"""
Packages the research manuscript, figures, and BibTeX into publication submission bundles for IntelliTwin.
"""

import os
import zipfile

def create_submission_zip():
    manuscript_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(manuscript_dir)
    zip_path_intelli = os.path.join(manuscript_dir, "intellitwin_journal_submission_package.zip")
    zip_path_uq = os.path.join(manuscript_dir, "uq_dt_journal_submission_package.zip")
    
    manuscript_files = [
        "INTELLITWIN_RESEARCH_PAPER_IEEE_FORMAT.docx",
        "INTELLITWIN_RESEARCH_PAPER_DOUBLE_COLUMN.pdf",
        "UQ_DT_RESEARCH_PAPER_IEEE_FORMAT.docx",
        "UQ_DT_RESEARCH_PAPER_DOUBLE_COLUMN.pdf",
        "research_paper_double_column.html",
        "RESEARCH_PAPER_INTELLITWIN.md",
        "references.bib",
    ]
    
    root_files = [
        "README.md",
        "requirements.txt",
        "COMMANDS_TO_RUN.txt",
    ]
    
    figures_to_include = [
        "fig1_rul_calibrated_intervals.png",
        "fig2_uncertainty_decomposition.png",
        "fig3_reliability_calibration.png",
        "fig4_pareto_coverage_width.png",
        "fig5_dss_cost_comparison.png",
    ]
    
    figures_dir = os.path.join(root_dir, "figures")
    
    for zip_path in [zip_path_intelli, zip_path_uq]:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for f in manuscript_files:
                p = os.path.join(manuscript_dir, f)
                if os.path.exists(p):
                    zipf.write(p, arcname=f)
                    
            for f in root_files:
                p = os.path.join(root_dir, f)
                if os.path.exists(p):
                    zipf.write(p, arcname=f)
                    
            for fig in figures_to_include:
                p = os.path.join(figures_dir, fig)
                if os.path.exists(p):
                    zipf.write(p, arcname=f"figures/{fig}")
                    
        print(f"Generated submission bundle: {zip_path} ({os.path.getsize(zip_path) / 1024:.1f} KB)")

if __name__ == "__main__":
    create_submission_zip()
