# Risk-aware GPU backfilling

Executable scheduling and probability counterexamples about a specific decision: **when can a queued job use idle GPUs without delaying an existing reservation?**

Runtime prediction becomes consequential when a scheduler acts on it. A bound can have high coverage across all jobs while performing poorly on the particular jobs admitted for backfilling. This repository makes the resource constraints, selection effect, and accumulation of risk explicit in small calculations that can be inspected end to end.

## Reservation mechanics

Consider four identical GPUs. At time zero, a running job occupies two GPUs until time 10. The job at the head of the queue needs all four GPUs, so its original reservation is time 10. A candidate backfill job requests the two idle GPUs and has a predicted runtime upper bound of 8.

Admission passes both a capacity condition and a timing condition:

$$
g_{\mathrm{running}}+g_{\mathrm{backfill}}\leq4,\qquad
U_{\mathrm{backfill}}\leq10.
$$

Jobs are non-preemptive, start at time zero in this example, have fixed durations, and do not interfere with one another. If the candidate's actual runtime is $T$, the protected job starts at

$$
t_{\mathrm{head}}=\max(10,T),\qquad
D=\max(0,t_{\mathrm{head}}-10),
$$

where $D$ is reservation delay.

| Actual backfill runtime | Protected job starts | Reservation delay | Allocated GPU fraction before time 10 |
|---|---:|---:|---:|
| 7 | 10 | 0 | 0.85 |
| 12 | 12 | 2 | 1.00 |

The allocation fraction is allocated GPU-time divided by available GPU-time over the original reservation window. In the first case it is $(2\times10+2\times7)/(4\times10)=0.85$. In the second case every GPU is allocated throughout that window, but the protected job starts late.

The comparison shows why an allocation metric alone cannot evaluate reservation protection. It also separates a bound violation, $T>8$, from a reservation violation, $T>10$: a duration between those thresholds would miss the predicted bound without delaying the head job. The script records the two replay cases above; the threshold distinction follows directly from the same equations.

## Coverage after the admission decision

Let $U(X)$ be a runtime bound based on observed job features $X$, and let $A$ indicate admission. Population coverage is

$$
\Pr(T\leq U(X)).
$$

For jobs whose bounds are actually used by the scheduler, the relevant quantity is

$$
\Pr(T\leq U(X)\mid A=1).
$$

The two probabilities need not agree. The script constructs a population with two groups:

* 90% of jobs never exceed their bounds.
* 10% exceed their bounds with probability 50%.
* The admission rule selects the second group.

The population miss rate is $0.9(0)+0.1(0.5)=0.05$, giving **95% marginal coverage**. Among admitted jobs, coverage is **50%**. Nothing about the population calculation is numerically wrong; selection changes which part of the population matters.

This construction isolates a feedback between prediction and decision. Evaluating a duration model only on all submitted jobs can conceal the error rate in the subset that determines reservation risk. The relevant experiment must record both predicted bounds and the decisions they induce.

## Multiple admitted jobs

Risk can also accumulate across several jobs. If three runtime-bound events each have coverage 0.95 and are independent, the probability that all three bounds hold is

$$
0.95^3=0.857375.
$$

The probability of at least one exceedance is therefore **14.2625%**. Independence is part of this numerical illustration, not an assumption established for workloads.

Without independence, the union bound gives an upper bound on any-exceedance probability by summing the individual miss probabilities. Applying that idea to an admission policy requires probabilities valid for the selected jobs under the relevant decision conditions. In addition, runtime-bound exceedance and actual reservation delay remain different events: spare time, resource overlap, and queue state determine whether an overrun affects the protected job.

## Run and inspect

~~~bash
python3 reservation_risk.py
~~~

The script uses only the Python standard library. Assertions check the resource feasibility, the two reservation delays, and the population miss-rate calculation. It writes [reservation_risk.json](reservation_risk.json), containing both replays, the selection example, and the three-job calculation.

The entire computation is in [reservation_risk.py](reservation_risk.py). Time units are arbitrary but consistent. Allocated GPU fraction describes reservations over time; it is not a measurement of device activity or computational throughput.

## Design of a workload evaluation

A chronological replay would fit duration bounds using past jobs, then feed identical arrivals and resource requests to each scheduling policy. First-come-first-served, deterministic backfilling, and a policy with an explicit reservation-risk budget would provide distinct decision baselines.

The evaluation should retain job-level admission decisions and report reservation-delay quantiles, waiting-time distributions, admitted-job coverage, and allocated GPU-time together. Queue conditions and job size can then reveal where a policy obtains its gains and where it spends risk. Correlated overruns should be included in that design, rather than inferred away through a product of marginal probabilities.

Those are specifications for a subsequent workload study. The repository's present evidence consists of synthetic counterexamples that identify what such a study needs to measure.
