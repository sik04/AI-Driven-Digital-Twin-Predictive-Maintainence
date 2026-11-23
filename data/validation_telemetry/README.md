# Bundled Validation Partition Telemetry for IntelliTwin Replay Demo

This directory contains pre-extracted, unperturbed historical telemetry observations strictly for the **validation partition engines** across the three supported NASA C-MAPSS sub-benchmarks:

- `FD001_validation.csv`: 10 validation engines (Units 3, 4, 17, 26, 37, 43, 59, 66, 74, 78; 2,050 total cycles)
- `FD002_validation.csv`: 26 validation engines (Units 9, 16, 21, 25, 30, 51, 54, 75, 94, 95, ...; 5,423 total cycles)
- `FD004_validation.csv`: 25 validation engines (Units 6, 8, 39, 43, 52, 65, 72, 76, 84, 98, ...; 5,926 total cycles)

## Scientific & Data Isolation Principles

1. **Strict Partition Demarcation**:
   - Telemetry is extracted exclusively from the validation partition defined by the frozen split manifests in `data/splits/*_engine_split_seed_2026.json`.
   - **No Training Engines**: Training engines are excluded.
   - **No Calibration Engines**: Calibration engines are excluded.
   - **Zero Held-Out Test Data**: Held-out test trajectories (`test_FD*.txt`, `RUL_FD*.txt`, and test partition engines) are strictly excluded and never bundled or exposed.

2. **No Oracle Information**:
   - The files contain only raw operational settings (`setting1`, `setting2`, `setting3`) and sensor readings (`s1` through `s21`) alongside `unit` and `cycle`.
   - No target labels, true RUL, terminal failure cycle, or lifecycle stage annotations are included.

3. **Cloud Deployment Portability**:
   - Bundling these lightweight validation trajectories (~2.2 MB total) enables complete cloud deployment (e.g. Render / Vercel) and local standalone execution without requiring users or cloud build environments to download the unbundled ~30 MB raw C-MAPSS benchmark archives.
