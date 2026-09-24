# Literature Corpus & Extraction Tools

This directory contains the foundational literature base and analytical scripts used to formulate the research gaps and ground the **UQ-DT** framework.

## Directory Structure

```text
literature/
├── papers/               # 15 foundational research papers in PDF format
│   ├── paper one.pdf     # Diana et al. (CEST 2025) - Urban Infrastructure DT Review
│   ├── paper 2.pdf       # Ali et al. (Digital Twin 2024) - Real-time structural updating
│   ├── paper 3.pdf       # Urban DTs Integration & Challenges Review
│   ├── paper4.pdf        # Hu Wei Doctoral Dissertation - DT & AI in Building Maintenance
│   ├── paper 5.pdf       # Bridge Monitoring & Sensor Integration
│   ├── paper 6.pdf       # Hosseinzadeh et al. (Mfg Letters 2023) - ALSTM-FCN PdM
│   ├── paper 7.pdf       # Multi-asset DT architectures
│   ├── paper 8.pdf       # Mousavi et al. (Remote Sensing 2024) - Bridge DT Scientometric Review
│   ├── paper 9.pdf       # Vibration-based structural health diagnosis
│   ├── paper 10.pdf      # AI-Driven Digital Twins for Urban Infrastructure Review
│   ├── paper 11.pdf      # AI-Augmented DT Architecture for PdM
│   ├── paper 12.pdf      # A New Era for Digital Twins: Progress & Industry Adoption
│   ├── paper 13.pdf      # Industrial IoT and edge analytics for DTs
│   ├── paper 14.pdf      # Wang et al. (MDPI Sensors 2026) - GA-Ensemble RUL
│   └── paper 15.pdf      # Federated Anomaly Detection for Industrial IoT
└── scripts/              # Automated PDF text extraction and gap mining utilities
    ├── extract_papers.py # Automated extraction of headers, abstracts, and limitation sections
    ├── deep_extract.py   # Targeted extraction of future work and research gaps
    ├── inspect_papers.py # Inspection CLI for extracted text summaries
    ├── show_gaps.py      # Formats and displays extracted gap statements
    ├── summarize_all.py  # Compiles full multi-paper overview
    └── summarize_extra.py# Additional deep synthesis summaries
```
