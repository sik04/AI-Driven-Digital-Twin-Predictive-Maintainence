"""
Synthetic and Empirical Degradation Data Generator for Digital Twin Telemetry.

Simulates physical asset degradation with non-linear wear dynamics, environmental
thermal masking (diurnal cycles), variable operational loading, and heteroscedastic
sensor noise, replicating conditions from CALCE (Paper 14), industrial testbeds (Paper 6),
and harsh environmental exposures (Paper 5).
"""

import numpy as np
import pandas as pd
from typing import Tuple, Dict, List, Optional


class InfrastructureDegradationSimulator:
    """
    Simulates multi-sensor time-series degradation trajectories for critical civil and
    mechanical infrastructure assets (e.g. bridge bearings, turbine blades, battery cells).
    """

    def __init__(self, random_seed: int = 42):
        self.rng = np.random.RandomState(random_seed)

    def generate_single_trajectory(
        self,
        asset_id: int,
        max_timesteps: int = 250,
        degradation_rate: Optional[float] = None,
        thermal_drift_amplitude: float = 1.8,
        thermal_shock_at: Optional[int] = None,
        operational_shock_at: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Generates a complete run-to-failure degradation trajectory for a single asset.
        """
        if degradation_rate is None:
            # Baseline asset degradation velocity with individual asset manufacturing variance
            degradation_rate = self.rng.uniform(0.008, 0.018)

        timesteps = np.arange(max_timesteps)
        
        # 1. Non-linear underlying physical wear kinetics (Paris-Erdogan / Exponential wear)
        # Wear D(t) evolves from 0.0 up to critical threshold (1.0)
        curvature = self.rng.uniform(1.8, 2.4)
        base_wear = (timesteps / (max_timesteps * 0.85)) ** curvature * (degradation_rate * 40.0)
        
        # Add random walk micro-wear increments
        wear_shocks = np.maximum(0, self.rng.normal(0, 0.003, size=max_timesteps))
        accumulated_shocks = np.cumsum(wear_shocks)
        total_wear = base_wear + accumulated_shocks

        # Inject sudden operational overload shock if specified (out-of-distribution event)
        if operational_shock_at and operational_shock_at < max_timesteps:
            shock_magnitude = self.rng.uniform(0.15, 0.25)
            total_wear[operational_shock_at:] += shock_magnitude

        # Health Index: H(t) in [0, 1]
        health_index = np.clip(1.0 - total_wear, 0.0, 1.0)

        # Determine exact failure point (H(t) <= 0.15)
        fail_indices = np.where(health_index <= 0.15)[0]
        if len(fail_indices) > 0:
            fail_step = fail_indices[0]
        else:
            fail_step = max_timesteps - 1

        # Ground truth Remaining Useful Life (RUL)
        rul = np.maximum(0, fail_step - timesteps)

        # 2. Environmental Diurnal Temperature Cycle (Thermal Drift)
        # Models day-night thermal swings that expand/contract materials (Paper 5 & 14)
        diurnal_period = 24.0  # 24-hour cycle
        ambient_temp = 20.0 + thermal_drift_amplitude * np.sin(2 * np.pi * timesteps / diurnal_period)
        ambient_temp += self.rng.normal(0, 0.25, size=max_timesteps)

        # Thermal shock: sudden heatwave or sensor freeze
        if thermal_shock_at and thermal_shock_at < max_timesteps:
            ambient_temp[thermal_shock_at : thermal_shock_at + 30] += 8.5

        # 3. Dynamic Operational Mechanical Load
        base_load = 50.0 + 10.0 * np.sin(2 * np.pi * timesteps / 120.0)
        load_jitter = self.rng.normal(0, 2.0, size=max_timesteps)
        operational_load = np.maximum(10.0, base_load + load_jitter)

        # 4. Multi-Sensor Telemetry Synthesis:
        # Sensor 1: Dynamic Strain Gauge (S1) - highly coupled with thermal expansion & structural wear
        thermal_expansion_coeff = 0.045
        strain_signal = (
            120.0 
            + (1.0 - health_index) * 180.0 
            + (ambient_temp - 20.0) * thermal_expansion_coeff * 200.0
            + (operational_load - 50.0) * 0.8
        )
        # Heteroscedastic noise: sensor jitter explodes as mechanical loose play increases
        strain_noise_std = 1.5 + 4.5 * (1.0 - health_index) ** 1.5
        sensor_strain = strain_signal + self.rng.normal(0, strain_noise_std, size=max_timesteps)

        # Sensor 2: Vibration RMS Accelerometer (S2) - sensitive to mechanical fatigue & bearing wear
        vibration_signal = 0.8 + 4.2 * ((1.0 - health_index) ** 2.2) + (operational_load / 100.0)
        vib_noise_std = 0.08 + 0.35 * (1.0 - health_index)
        sensor_vibration = vibration_signal + self.rng.normal(0, vib_noise_std, size=max_timesteps)

        # Sensor 3: Acoustic Emission Energy (S3) - detects active micro-crack friction
        ae_signal = 15.0 + 65.0 * ((1.0 - health_index) ** 3.0)
        ae_noise_std = 1.0 + 5.0 * (1.0 - health_index)
        sensor_ae = np.maximum(0, ae_signal + self.rng.normal(0, ae_noise_std, size=max_timesteps))

        # Sensor 4: Surface Operating Temperature (S4) - frictional heating + ambient
        sensor_temp = ambient_temp + 12.0 * (1.0 - health_index) ** 1.8 + (operational_load * 0.05)

        # Cut trajectory at failure step + 5 buffer points (asset retired)
        valid_length = min(max_timesteps, fail_step + 5)

        df = pd.DataFrame({
            "asset_id": asset_id,
            "timestep": timesteps[:valid_length],
            "sensor_strain": sensor_strain[:valid_length],
            "sensor_vibration": sensor_vibration[:valid_length],
            "sensor_acoustic": sensor_ae[:valid_length],
            "sensor_temp": sensor_temp[:valid_length],
            "ambient_temp": ambient_temp[:valid_length],
            "operational_load": operational_load[:valid_length],
            "health_index": health_index[:valid_length],
            "true_rul": rul[:valid_length],
            "aleatoric_noise_level": strain_noise_std[:valid_length],
        })

        return df

    def generate_fleet_dataset(
        self,
        num_train_assets: int = 24,
        num_calib_assets: int = 8,
        num_test_nominal: int = 10,
        num_test_ood: int = 6,
    ) -> Dict[str, pd.DataFrame]:
        """
        Generates distinct splits for training, conformal calibration, nominal testing,
        and out-of-distribution (OOD) stress testing.
        """
        asset_counter = 0

        # Training fleet (nominal conditions)
        train_dfs = []
        for _ in range(num_train_assets):
            df = self.generate_single_trajectory(asset_id=asset_counter)
            train_dfs.append(df)
            asset_counter += 1
        train_data = pd.concat(train_dfs, ignore_index=True)

        # Calibration fleet (nominal conditions, held out for Conformal Prediction)
        calib_dfs = []
        for _ in range(num_calib_assets):
            df = self.generate_single_trajectory(asset_id=asset_counter)
            calib_dfs.append(df)
            asset_counter += 1
        calib_data = pd.concat(calib_dfs, ignore_index=True)

        # Test fleet - In-Distribution (Nominal)
        test_nominal_dfs = []
        for _ in range(num_test_nominal):
            df = self.generate_single_trajectory(asset_id=asset_counter)
            test_nominal_dfs.append(df)
            asset_counter += 1
        test_nominal_data = pd.concat(test_nominal_dfs, ignore_index=True)

        # Test fleet - Out-of-Distribution (OOD: Thermal Shocks & Overload)
        test_ood_dfs = []
        for _ in range(num_test_ood):
            df = self.generate_single_trajectory(
                asset_id=asset_counter,
                thermal_drift_amplitude=4.5,
                thermal_shock_at=int(self.rng.uniform(40, 80)),
                operational_shock_at=int(self.rng.uniform(60, 110)),
            )
            test_ood_dfs.append(df)
            asset_counter += 1
        test_ood_data = pd.concat(test_ood_dfs, ignore_index=True)

        return {
            "train": train_data,
            "calib": calib_data,
            "test_nominal": test_nominal_data,
            "test_ood": test_ood_data,
        }


def extract_feature_matrix(
    df: pd.DataFrame,
    feature_cols: Optional[List[str]] = None,
    target_col: str = "true_rul",
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extracts numerical feature array X and target array y from a dataframe.
    """
    if feature_cols is None:
        feature_cols = [
            "sensor_strain",
            "sensor_vibration",
            "sensor_acoustic",
            "sensor_temp",
            "ambient_temp",
            "operational_load",
        ]
    X = df[feature_cols].values
    y = df[target_col].values
    return X, y
