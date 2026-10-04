# Systematic Literature Search Protocol

## 1. Purpose and Scope

This protocol establishes the scientific methodology for Phase 1 (Systematic Literature Review) of the IntelliTwin project, conducted jointly by Mayank Singh, Shiksha Pandey, and Ruchi Gupta. It governs how academic literature is searched, screened, extracted, and synthesized to ensure all claims are traceable to peer-reviewed scholarly evidence.

---

## 2. Multi-Source Search Strategy and Provenance

In adherence to strict academic honesty, the literature review employs a transparent multi-source retrieval framework:

1. **Curated Repository Seed Corpus**:
   - 15 research papers initially assembled in the repository under `papers/` covering digital twins, structural health monitoring, manufacturing anomaly detection, and predictive maintenance.
2. **Targeted Closest-Work Database & API Searches**:
   - Programmatic metadata queries via the Crossref REST API (`https://api.crossref.org/works/`).
   - Programmatic preprint queries via the arXiv API (`https://export.arxiv.org/api/query`).
   - Targeted scholarly grounding via publisher DOI resolvers (IEEE Xplore, ScienceDirect/Elsevier, Wiley, SpringerLink, MDPI, Taylor & Francis).
3. **Backward and Forward Citation Tracing**:
   - Backward reference mining of high-priority closest works (e.g., tracing foundational C-MAPSS dataset literature from Saxena et al., 2008, and conformal prognostics from Javanmardi & Hüllermeier, 2023).
4. **Institutional Repository & Artifact Verification Audits**:
   - Querying institutional repositories (e.g., Egypt-Japan University of Science and Technology, Nanyang Technological University) and open science repositories (Zenodo) to verify candidate theses and software artifacts before bibliographic inclusion.

---

## 3. Executed Search Queries and Dates

All searches were executed on **October 4, 2026**.

### Canonical and Targeted Query Strings Executed
- **Query 1 (Closest-Work Intersection)**:
  `("remaining useful life" OR RUL) AND ("conformal prediction" OR "prediction interval" OR "uncertainty calibration" OR "conditional coverage") AND ("maintenance decision" OR "predictive maintenance" OR "maintenance cost")`
- **Query 2 (Aero-Engine Regime & Degradation Diagnostics)**:
  `("conformal prediction" OR "prediction interval") AND ("C-MAPSS" OR turbofan) AND ("degradation stage" OR "life stage" OR "operating regime" OR "distribution shift")`
- **Query 3 (Calibrated Uncertainty in PdM)**:
  `("calibrated uncertainty" OR "conformal calibration") AND ("optimal maintenance scheduling" OR "risk-aware maintenance") AND ("turbofan" OR "aero-engine")`
- **Query 4 (Digital Twin + RUL State of the Art)**:
  `"Digital Twin" AND "Remaining Useful Life" AND ("C-MAPSS" OR turbofan)`

---

## 4. Eligibility and Screening Criteria

### Inclusion Criteria (IC)
1. **IC1**: Peer-reviewed journal articles, conference proceedings, verifiable doctoral dissertations, or indexed technical preprints published in English.
2. **IC2**: Empirical investigation of remaining useful life (RUL) estimation, degradation trajectory modeling, or predictive maintenance using engineering telemetry (specifically NASA C-MAPSS or rotating machinery benchmarks).
3. **IC3**: Formal presentation of uncertainty quantification techniques (e.g., conformal prediction, quantile regression, Bayesian neural networks, deep ensembles) OR explicit maintenance decision support policies (e.g., threshold replacement, cost-rate optimization, RL scheduling).
4. **IC4**: Documented quantitative evaluation metrics (e.g., RMSE, NASA scoring metric, PICP, MPIW, lifecycle cost).

### Exclusion Criteria (EC)
1. **EC1**: Short extended abstracts (<4 pages), promotional whitepapers, unverified blog posts, or commercial document-sharing uploads (e.g., Scribd) lacking institutional catalog verification.
2. **EC2**: Studies lacking empirical validation on reproducible engineering datasets or physics simulations.
3. **EC3**: Pure discrete fault classification papers without prognostic RUL degradation modeling.
4. **EC4**: Duplicate publications of identical research findings.
5. **EC5**: Candidate software artifacts or DOI records returning HTTP 404 or lacking verifiable peer-reviewed text.

---

## 5. Deduplication and Verification Procedure

1. **DOI and Canonical Identifier Normalization**: All retrieved candidates are stripped of URL prefixes and matched against Crossref / arXiv registries.
2. **Title and Author Cross-Matching**: Exact title matching and Levenshtein distance checks to eliminate preprint-journal duplicate records.
3. **Integrity Audit**:
   - If a work cannot be verified via Crossref, publisher DOI, official university repository, or arXiv, it is tagged as an `Unverified Lead` in `research/literature/screening_log.csv` and excluded from `paper/references.bib`.

---

## 6. Documented Limitations of Search Access

- **Database Access Limitation**: Direct bulk programmatic scraping access to subscription-restricted databases (e.g., Scopus full-text API, Web of Science institutional bulk downloads) was restricted by local network authentication environments.
- **Surveillance Status**: Literature surveillance was conducted via public open APIs (Crossref REST API, arXiv API, Semantic Scholar, and official publisher landing pages).
- **Milestone Governance**: In accordance with scientific integrity guidelines, because institutional bulk database screening is an ongoing surveillance process, **Phase 1 remains marked as "In Progress"** throughout early research phases rather than falsely declared permanently closed.
