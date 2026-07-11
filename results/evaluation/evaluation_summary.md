# ARES Evaluation Summary

## Exploration Comparison

| Agent | Episodes | Success Rate | Average Reward | Average Steps | Average Visited States |
|---|---:|---:|---:|---:|---:|
| PPO | 3 | 100.00% | 17.50 | 1.00 | 2.00 |
| RANDOM | 3 | 33.33% | -1.83 | 8.00 | 1.67 |

## Self-Healing Fault Injection

- Injected faults: 6
- Healed faults: 6
- Healing success rate: 100.00%
- Executed replacements: 6
- Average selected score: 0.9395

## Interpretation

These results validate the integration of the ARES browser, exploration, self-healing, and script-generation components on controlled smoke-test and synthetic fault-injection scenarios.

They should not be treated as evidence for the full conference evaluation until the experiments are repeated on all selected systems under test, with the planned seeds, fault sets, and metrics.
