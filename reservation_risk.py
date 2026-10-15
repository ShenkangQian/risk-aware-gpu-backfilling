"""Synthetic scheduling and probability counterexamples, not workload results."""
import json
from pathlib import Path

capacity = 4
running_gpus = 2
running_finish = 10
head_request = 4
reservation_original = 10
backfill_gpus = 2
backfill_upper = 8
assert running_gpus + backfill_gpus <= capacity
assert backfill_upper <= reservation_original

def replay(actual_runtime):
    # Both running and backfill jobs start at 0; the protected head requires all GPUs.
    actual_head_start = max(running_finish, actual_runtime)
    return {
        'actual_backfill_runtime': actual_runtime,
        'original_reservation': reservation_original,
        'actual_head_start': actual_head_start,
        'reservation_delay': max(0, actual_head_start - reservation_original),
        'runtime_exceeds_upper': actual_runtime > backfill_upper,
        'allocated_gpu_fraction_before_original_reservation': (
            running_gpus * reservation_original + backfill_gpus * min(actual_runtime, reservation_original)
        ) / (capacity * reservation_original)
    }

safe = replay(7)
overrun = replay(12)
assert safe['reservation_delay'] == 0
assert overrun['reservation_delay'] == 2
population_miss = 0.9 * 0.0 + 0.1 * 0.5
selected_miss = 0.5
assert abs(population_miss - 0.05) < 1e-12
result = {
    'status': 'synthetic scheduling counterexample',
    'units': 'arbitrary consistent time units',
    'assumptions': 'four identical GPUs, non-preemptive fixed-duration jobs, no interference or failures',
    'safe_backfill': safe,
    'overrun_backfill': overrun,
    'selection_counterexample': {
        'overall_marginal_bound_coverage': 1 - population_miss,
        'selected_subgroup_bound_coverage': 1 - selected_miss,
        'construction': '90% group never exceeds bound; 10% group exceeds with probability 50%; scheduler selects latter group'
    },
    'independent_three_job_illustration': {
        'individual_coverage': 0.95,
        'all_three_coverage_if_independent': 0.95 ** 3,
        'at_least_one_exceedance_if_independent': 1 - 0.95 ** 3,
        'warning': 'This is an independence-based illustration, not an assumption about real jobs.'
    },
    'limits': 'Allocated GPU fraction is not measured hardware utilization. No proposed scheduler improvement is demonstrated.'
}
Path(__file__).with_name('reservation_risk.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
