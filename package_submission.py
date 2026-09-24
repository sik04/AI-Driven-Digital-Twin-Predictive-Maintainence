"""
Packages the research manuscript, figures, and BibTeX into a publication submission bundle.
"""

import os
import zipfile

def create_submission_zip():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_path = os.path.join(base_dir, "uq_dt_journal_submission_package.zip")
    
    files_to_include = [
        "main.tex",
        "references.bib",
        "RESEARCH_PAPER_GAP3_UQ_DT.md",
        "README.md",
        "requirements.txt",
    ]
    
    figures_to_include = [
        "figures/fig1_rul_calibrated_intervals.png",
        "figures/fig2_uncertainty_decomposition.png",
        "figures/fig3_reliability_calibration.png",
        "figures/fig4_pareto_coverage_width.png",
        "figures/fig5_dss_cost_comparison.png",
    ]
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in files_to_include:
            p = os.path.join(base_dir, f)
            if os.path.exists(p):
                zipf.write(p, arcname=f)
                print(f"Added: {f}")
                
        for fig in figures_to_include:
            p = os.path.join(base_dir, fig)
            if os.path.exists(p):
                zipf.write(p, arcname=fig)
                print(f"Added: {fig}")
                
    print(f"\nSuccessfully generated submission bundle: {zip_path}")
    print(f"Archive size: {os.path.getsize(zip_path) / 1024:.1f} KB")

if __name__ == "__main__":
    create_submission_zip()
