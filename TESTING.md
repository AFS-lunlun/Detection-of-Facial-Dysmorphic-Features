# Testing

Run numerical and input-integrity tests from the repository root:

```bash
python -m unittest discover -s tests -v
```

The test suite covers binary metrics, AUC ties and ranking, undefined ratios,
invalid probabilities, participant aggregation, conflicting labels, duplicate
samples, participant-disjoint splitting, deterministic seeded bootstrap,
small-sample interval handling, PPV scenarios, path restrictions and exact
cross-partition image duplicates.

Synthetic command-line examples exercise partitioning, participant/image-level
evaluation, ROC/calibration export, PPV scenarios and model comparison. Example
results must not be interpreted as clinical findings.

Numerical tests and example commands were exercised with Python 3.12; figure
exports were exercised with matplotlib 3.11.2. The CI workflow targets Python
3.10 and 3.12. Dependency constraints define the supported installation range.

The public-file scanner flags common private paths, credentials and unexpected
artifacts. It does not establish that a dataset is anonymous or that evaluation
is statistically independent.
