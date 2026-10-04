# Systematic Literature Search Protocol

## 1. Purpose and Scope

This protocol establishes the scientific methodology for Phase 1 (Systematic Literature Review) of the IntelliTwin project. It governs how academic literature is searched, screened, extracted, and synthesized to ensure all claims are traceable to peer-reviewed scholarly evidence.

---

## 2. Research Databases and Search Strategy

Searches will be conducted systematically across major indexed scientific repositories:
- **IEEE Xplore**
- **ScienceDirect / Elsevier**
- **SpringerLink**
- **ACM Digital Library**
- **Google Scholar / Semantic Scholar**
- **arXiv (preprints strictly audited for methodology)**

### Canonical Query Strings (Subject to refinement in Phase 1)
- Query A (Prognostics & Deep Learning):
  `("predictive maintenance" OR "remaining useful life" OR "RUL") AND ("deep learning" OR "LSTM" OR "transformer" OR "temporal convolutional network") AND ("turbofan" OR "C-MAPSS")`
- Query B (Uncertainty Quantification):
  `("remaining useful life" OR "prognostics") AND ("uncertainty quantification" OR "conformal prediction" OR "prediction intervals" OR "Bayesian neural network")`
- Query C (Digital Twin & Decision Support):
  `("digital twin" AND "predictive maintenance") AND ("decision support" OR "maintenance scheduling")`

---

## 3. Eligibility Criteria

### Inclusion Criteria (IC)
1. **IC1**: Peer-reviewed journal articles, flagship conference proceedings, or verifiable benchmark preprints published in English.
2. **IC2**: Empirical investigation of remaining useful life (RUL) estimation or degradation modeling on engineering benchmark datasets (e.g., NASA C-MAPSS, PRONOSTIA).
3. **IC3**: Formal presentation of uncertainty quantification techniques (e.g., Bayesian, ensemble, conformal, quantile regression) OR explicit prognostic decision support policies.
4. **IC4**: Documented quantitative evaluation metrics (e.g., RMSE, NASA scoring metric, coverage, interval width).

### Exclusion Criteria (EC)
1. **EC1**: Short extended abstracts (<4 pages), opinion pieces, non-technical promotional whitepapers, or unindexed blog posts.
2. **EC2**: Studies lacking empirical validation on reproducible engineering datasets.
3. **EC3**: Pure fault diagnosis papers without prognostic or RUL temporal progression modeling.
4. **EC4**: Duplicate publications of identical research findings.

---

## 4. Screening and Extraction Workflow

1. **Identification**: Execute canonical queries and log all retrieval records in `research/literature/screening_log.csv`.
2. **Title & Abstract Screening**: Screen against IC/EC and mark decisions (`Include` / `Exclude` with reason).
3. **Full-Text Evaluation**: Review full text for eligible records and verify scholarly identifiers (DOI, venue, authors).
4. **Data Extraction**: Populate `research/literature/literature_matrix.csv` with extracted methodological parameters:
   - Method category & architecture
   - Dataset & operating conditions
   - Split protocol (engine-level vs. cycle-level)
   - Evaluation metrics & numerical outcomes
   - Reported limitations & failure modes
   - Open source code and data availability

---

## 5. Scholarly Integrity Rules

- **Zero Fabrication**: No citation, author, DOI, or performance number may be fabricated.
- **Traceability**: Every assertion in the literature review must cite the corresponding `literature_matrix.csv` entry.
- **Gaps Derived from Evidence**: Research gaps must arise organically from the synthesized limitations of existing work, rather than being manufactured to justify preconceived architectural choices.
