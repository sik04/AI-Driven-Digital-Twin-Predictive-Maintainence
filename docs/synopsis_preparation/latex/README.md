# IntelliTwin LaTeX Research Documentation Package

This directory contains the modular LaTeX sources for IntelliTwin's research documentation deliverables, structured for maintainability and direct integration of verified experimental results.

## Directory Structure

```
docs/synopsis_preparation/latex/
├── README.md                      # Compilation guide and architecture
├── shared/
│   ├── notation.tex               # Universal mathematical notation macros
│   └── hypotheses.tex             # Authoritative hypothesis definitions and decision rules
├── hypotheses/
│   └── main.tex                   # Standalone Hypothesis Appendix entry point
├── synopsis/
│   ├── main.tex                   # IEEEtran Research Synopsis entry point
│   └── sections/                  # Modular synopsis sections
│       ├── introduction.tex
│       ├── problem_objectives.tex
│       ├── related_work.tex
│       ├── methodology.tex
│       ├── evaluation.tex
│       ├── status_results.tex
│       └── limitations_conclusion.tex
├── paper/
│   ├── main.tex                   # IEEEtran Conference/Journal Paper entry point
│   └── sections/                  # Modular paper sections
│       ├── introduction.tex
│       ├── related_work.tex
│       ├── problem_formulation.tex
│       ├── methodology.tex
│       ├── experimental_setup.tex
│       ├── results.tex
│       ├── discussion.tex
│       └── conclusion.tex
└── thesis/
    ├── main.tex                   # Academic Dissertation (report class) entry point
    └── chapters/                  # Modular dissertation chapters
        ├── introduction.tex
        ├── literature_review.tex
        ├── problem_hypotheses.tex
        ├── methodology.tex
        ├── implementation.tex
        ├── experimental_design.tex
        ├── results_discussion.tex
        ├── limitations_conclusion.tex
        └── reproducibility_appendix.tex
```

## Compilation Instructions

The LaTeX documents can be compiled using either the modern self-contained `tectonic` compiler or standard `latexmk` / `pdflatex` pipelines.

### Using Tectonic (Recommended)

From the repository root:

1. **Hypothesis Appendix**:
   ```powershell
   tectonic docs/synopsis_preparation/latex/hypotheses/main.tex -o docs/synopsis_preparation/previews/
   Move-Item docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/hypotheses_appendix.pdf -Force
   ```

2. **Research Synopsis**:
   ```powershell
   tectonic docs/synopsis_preparation/latex/synopsis/main.tex -o docs/synopsis_preparation/previews/
   Move-Item docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/synopsis_draft.pdf -Force
   ```

3. **IEEE Paper Draft**:
   ```powershell
   tectonic docs/synopsis_preparation/latex/paper/main.tex -o docs/synopsis_preparation/previews/
   Move-Item docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/ieee_paper_draft.pdf -Force
   ```

4. **Thesis Draft**:
   ```powershell
   tectonic docs/synopsis_preparation/latex/thesis/main.tex -o docs/synopsis_preparation/previews/
   Move-Item docs/synopsis_preparation/previews/main.pdf docs/synopsis_preparation/previews/thesis_draft.pdf -Force
   ```

### Using Latexmk / PDFLaTeX

From each document directory (`docs/synopsis_preparation/latex/{synopsis,paper,thesis,hypotheses}/`):
```bash
latexmk -pdf -interaction=nonstopmode main.tex
```

## Shared Bibliography

All documents utilize the independently audited, verified bibliography located at:
`docs/synopsis_preparation/references_verified.bib`

No edits are made to the root `paper/references.bib`.
