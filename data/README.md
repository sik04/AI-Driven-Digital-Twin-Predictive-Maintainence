# C-MAPSS Dataset Setup & Directory Structure

This directory contains local raw dataset files and machine-readable reproducible partition manifests for the IntelliTwin research project.

---

## 1. Raw Dataset Placement Instructions

To set up the NASA Commercial Modular Aero-Propulsion System Simulation (C-MAPSS) dataset locally:

1. Download the official NASA C-MAPSS degradation benchmark dataset.
2. Extract the archive contents locally on your machine.
3. Move all canonical dataset files into the directory:

   ```text
   data/raw/cmapss/
   ```

4. Verify that `data/raw/cmapss/` contains the following 14 expected canonical files:

   ```text
   data/raw/cmapss/
   ├── train_FD001.txt
   ├── test_FD001.txt
   ├── RUL_FD001.txt
   ├── train_FD002.txt
   ├── test_FD002.txt
   ├── RUL_FD002.txt
   ├── train_FD003.txt
   ├── test_FD003.txt
   ├── RUL_FD003.txt
   ├── train_FD004.txt
   ├── test_FD004.txt
   ├── RUL_FD004.txt
   ├── readme.txt
   └── Damage Propagation Modeling.pdf
   ```

---

## 2. Git Tracking Policy

- **Raw Dataset Files**: All files inside `data/raw/` are intentionally **Git-ignored** to prevent repository bloat and enforce clean open-science data separation.
- **Reproducible Manifests**: Machine-readable dataset partition manifests, metadata, and research protocol documentation are tracked in Git.

---

## 3. Reproducible Engine Split Manifest

The pre-specified, engine-level stratified partition manifest for FD002 (Seed 2026, lifetime quartile stratification) is committed and tracked at:

```text
data/splits/fd002_engine_split_seed_2026.json
```

### Partition Summary (FD002 Primary Dataset)
- **Train Partition**: 130 engines (50%)
- **Calibration Partition**: 52 engines (20%)
- **Validation Partition**: 26 engines (10%)
- **Held-out Test Partition**: 52 engines (20%)
- **Total Unique Engines**: 260 engines (100% disjoint isolation)
