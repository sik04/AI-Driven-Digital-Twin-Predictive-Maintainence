"""
Catastrophic Failure Detection and Severe Risk Evaluation Engine for IntelliTwin.
Evaluates early warning lead times, critical zone detection, missed catastrophic
failures, and false alarm rates across run-to-failure engine trajectories.
"""

import numpy as np


class CatastrophicFailureEvaluator:
    """Evaluates early warning and catastrophic risk handling performance."""

    def __init__(self, critical_threshold_cycles=20, warning_threshold_cycles=45):
        self.critical_threshold_cycles = critical_threshold_cycles
        self.warning_threshold_cycles = warning_threshold_cycles

    def evaluate_trajectories(self, trajectories):
        """Evaluate a list of run-to-failure engine trajectories.
        Each trajectory is a dict with:
            'unit': int
            'cycles': array of cycle indices
            'rul_true': array of true RUL values
            'rul_pred': array of predicted RUL values
            'rul_lower': array of conformal lower bounds
        """
        lead_times = []
        missed_critical = 0
        total_critical = 0
        false_warnings = 0
        total_healthy_checks = 0

        for traj in trajectories:
            rul_true = np.asarray(traj["rul_true"])
            rul_pred = np.asarray(traj["rul_pred"])
            cycles = np.asarray(traj["cycles"])

            # 1. Detection Lead Time: how many cycles before actual failure was warning first triggered?
            # Warning triggers when predicted RUL (or lower bound) falls below warning_threshold_cycles
            warn_indices = np.where(rul_pred <= self.warning_threshold_cycles)[0]
            if len(warn_indices) > 0:
                first_warn_idx = warn_indices[0]
                lead_time = rul_true[first_warn_idx]
                lead_times.append(float(lead_time))
            else:
                lead_times.append(0.0)

            # 2. Critical Zone Verification: in the final critical_threshold_cycles, did the model alarm?
            crit_mask = (rul_true <= self.critical_threshold_cycles)
            if np.any(crit_mask):
                total_critical += 1
                # If during the critical zone the model NEVER predicted critical or warning, it's a catastrophic miss
                crit_pred = rul_pred[crit_mask]
                if not np.any(crit_pred <= self.critical_threshold_cycles * 1.2):
                    missed_critical += 1

            # 3. False Alarm Rate during early healthy operation (RUL > 70)
            healthy_mask = (rul_true > 70)
            if np.any(healthy_mask):
                total_healthy_checks += int(np.sum(healthy_mask))
                false_alarms_in_traj = np.sum(rul_pred[healthy_mask] <= self.critical_threshold_cycles)
                false_warnings += int(false_alarms_in_traj)

        missed_rate = float(missed_critical / max(1, total_critical))
        false_alarm_rate = float(false_warnings / max(1, total_healthy_checks))
        mean_lead_time = float(np.mean(lead_times)) if lead_times else 0.0
        min_lead_time = float(np.min(lead_times)) if lead_times else 0.0

        return {
            "total_engines_evaluated": len(trajectories),
            "mean_warning_lead_time_cycles": mean_lead_time,
            "min_warning_lead_time_cycles": min_lead_time,
            "missed_catastrophic_failures": int(missed_critical),
            "missed_catastrophic_rate": missed_rate,
            "false_alarm_count": int(false_warnings),
            "false_alarm_rate": false_alarm_rate,
            "catastrophic_prevention_success_rate": 1.0 - missed_rate,
        }
