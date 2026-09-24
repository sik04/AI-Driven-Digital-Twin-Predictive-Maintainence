"""
Packages the research manuscript, figures, and BibTeX into a publication submission bundle.
"""

import os
import zipfile

def create_submission_zip():
    manuscript_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(manuscript_dir)
    zip_path = os.path.join(manuscript_dir, "uq_dt_journal_submission_package.zip")
    
    manuscript_files = [
        "main.tex",
        "references.bib",
        "RESEARCH_PAPER_GAP3_UQ_DT.md",
    ]
    
    root_files = [
        "README.md",
        "requirements.txt",
    ]
    
    figures_to_include = [
        "fig1_rul_calibrated_intervals.png",
        "fig2_uncertainty_decomposition.png",
        "fig3_reliability_calibration.png",
        "fig4_pareto_coverage_width.png",
        "fig5_dss_cost_comparison.png",
    ]
    
    figures_dir = os.path.join(root_dir, "figures")
    
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
        for f in manuscript_files:
            p = os.path.join(manuscript_dir, f)
            if os.path.exists(p):
                zipf.write(p, arcname=f)
                print(f"Added manuscript file: {f}")
                
        for f in root_files:
            p = os.path.join(root_dir, f)
            if os.path.exists(p):
                zipf.write(p, arcname=f)
                print(f"Added root file: {f}")
                
        for fig in figures_to_include:
            p = os.path.join(figures_dir, fig)
            if os.path.exists(p):
                zipf.write(p, arcname=f"figures/{fig}")
                print(f"Added figure: figures/{fig}")
                
    print(f"\nSuccessfully generated submission bundle: {zip_path}")
    print(f"Archive size: {os.path.getsize(zip_path) / 1024:.1f} KB")

if __name__ == "__main__":
    create_submission_zip()
