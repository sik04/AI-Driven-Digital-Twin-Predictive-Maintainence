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

## 3. Reproducible Engine Split Manifests

Pre-specified, engine-level stratified partition manifests (Seed 2026, lifetime quartile stratification) are committed and tracked at:

- **FD001**: `data/splits/fd001_engine_split_seed_2026.json` (50 / 20 / 10 / 20 engines; Total: 100)
- **FD002**: `data/splits/fd002_engine_split_seed_2026.json` (130 / 52 / 26 / 52 engines; Total: 260)
- **FD004**: `data/splits/fd004_engine_split_seed_2026.json` (124 / 50 / 25 / 50 engines; Total: 249)

### Partition Ratios (50% Train / 20% Calibration / 10% Validation / 20% Test)
- All partitions enforce 100% engine-level disjoint isolation.
- Preprocessing scalers, K-means operating-regime models, and feature normalization parameters are fit on training partition engines ONLY.

