# Facial phenotype classifier analysis

Python tools for participant-level data partitioning and statistical evaluation of
binary facial phenotype classifiers. The package accepts classification labels
and positive-class probabilities, calculates performance metrics, and exports
tables and figures for research reporting.

[中文说明](README.zh-CN.md)

## Analysis functions

- Class-stratified, participant-disjoint training/validation partitioning.
- Participant-overlap checks and optional exact image-duplicate checks.
- Image-level and participant-level evaluation.
- ROC/AUC, confusion matrices, accuracy, precision, sensitivity, specificity,
  F1-score, PPV, NPV and Brier score.
- Participant-level bootstrap confidence intervals.
- Descriptive calibration summaries and figures.
- Model comparisons on identical evaluation samples.
- Hypothetical prevalence-based PPV scenarios.

The analysis commands support data partitioning, evaluation tables and research figures.

## Installation

Python 3.10 or later is required. Numerical analyses and unit tests use the Python
standard library. Figure export additionally requires matplotlib.

```bash
python -m venv .venv
# Activate the virtual environment using your operating system's standard command.
python -m pip install -r requirements.txt
python analysis.py --help
```

Dependencies are specified in `requirements.txt` and `pyproject.toml`. Record the
software versions used for each research analysis. Before sharing an environment
export, check it for local paths or other private information.

## Input data

Use one manifest or prediction file per binary classification task. Label `1`
denotes the positive outcome; `probability` denotes its predicted probability.
Participant identifiers must be consistent across all images belonging to the
same participant. Store study inputs privately and use randomly assigned opaque
tokens in the analysis files. Keep identity mappings outside the repository.

See [input formats](docs/INPUT_SCHEMA.md) for the required columns and validation
rules. No participant-level study data, photographs or trained model weights are
distributed with this code. The example files contain synthetic data only.

## Example analysis

```bash
python analysis.py audit --manifest examples/synthetic_manifest.csv --output outputs/example_audit.json
python analysis.py split --manifest examples/synthetic_manifest.csv --seed 20261123 --output outputs/example_partition.csv
python analysis.py evaluate --predictions examples/synthetic_predictions.csv --split val --unit participant --bootstrap 200 --plots --output outputs/example_participant
python analysis.py evaluate --predictions examples/synthetic_predictions.csv --split val --unit image --plots --output outputs/example_image
python analysis.py ppv --sensitivity 0.90 --specificities 1.0 0.999 0.99 --prevalences 0.001 0.01 0.05 0.10 --output outputs/example_ppv.csv
```

Example probabilities and labels are artificial and illustrate the file formats
and analysis commands. No example photographs are included. The manifest's image
paths are placeholders. Generated example results are not clinical findings.

## Analyze study predictions

```bash
python analysis.py audit --manifest private_data/manifest.csv --data-root private_data --output outputs/partition_audit.json
python analysis.py evaluate --predictions private_data/predictions_resnet18.csv --unit participant --threshold 0.5 --bootstrap 2000 --output outputs/resnet18
```

Audit the complete training/validation/test manifest before evaluation. A file
containing only validation predictions cannot establish absence of training-set
participant overlap. Exact image hashes do not identify near-duplicates or one
participant represented by multiple tokens.

A new partition requires model training on that partition before evaluation.
Use a prespecified classification threshold and document the random seed, label
mapping and aggregation rule. Participant-level evaluation uses the arithmetic
mean of positive-class image probabilities. Algorithm definitions and statistical
assumptions are described in [Methods](docs/METHODS.md).

## Compare models

Generate one evaluation report per model, then run:

```bash
python analysis.py compare --reports ResNet18=outputs/resnet18/metrics.json ResNet34=outputs/resnet34/metrics.json ResNet50=outputs/resnet50/metrics.json --output outputs/comparison
```

Model comparisons require identical evaluation sample/group/label fingerprints,
evaluation units, thresholds, partitions and declared evaluation roles.

## Statistical interpretation

Evaluation on a validation set used for checkpoint selection is developmental
validation. Participant bootstrap intervals do not remove model-selection bias,
validation reuse or image-source confounding. The `independent` evaluation role
must be supported by the study design; software cannot establish independence.

PPV scenarios require explicit sensitivity, specificity and target-prevalence
assumptions. Prevalence must refer to the classifier's positive outcome. Zero
observed false positives in a small sample does not establish perfect population
specificity or clinical PPV.

## Testing

```bash
python -m unittest discover -s tests -v
python tools/check_public_files.py
```

See [testing](TESTING.md). Automated checks cover numerical calculations and input
integrity. The GitHub Actions workflow runs the test suite on supported Python
versions.

## Data and code availability

This repository distributes analysis code and synthetic examples. Individual-level
study data and facial photographs are not included. Manuscript wording for this
code package is provided in [Code availability](docs/CODE_AVAILABILITY.md).

Only upload the contents of this code directory. Review staged files before
publication. Ignore rules do not remove already tracked files or protect files
manually uploaded through a browser. See [public-release guidance](docs/PUBLIC_RELEASE.md).

## License and references

Code is distributed under the MIT license. The license does not cover third-party
datasets, participant images or model weights.

- [CLAIM reporting guidance](https://pmc.ncbi.nlm.nih.gov/articles/PMC11304031/)
- [FFHQ dataset documentation](https://github.com/NVlabs/ffhq-dataset)
