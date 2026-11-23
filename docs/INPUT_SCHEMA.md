# Private input schemas

CSV files must be UTF-8 with a header. Unknown columns are rejected. Do not add
names, dates of birth, medical record numbers or original photo identifiers.

| Manifest column | Meaning |
| --- | --- |
| sample_id | Unique opaque token matching `sample_[a-z0-9]+` |
| group_id | Opaque token matching `group_[a-z0-9]+`, stable across one person's photos |
| image_path | Relative POSIX path under a private data root, no absolute path or `..` |
| label | `1` = target positive outcome, `0` = reference/negative outcome |
| split | `train`, `val`, `test`; omitted/ignored when creating a new split |
| data_kind | Optional `private` or `synthetic` |

Probability CSV columns: `sample_id,group_id,label,split,probability` plus optional
`data_kind`. Probability must be finite, in [0,1] and correspond to the positive
class. No image-path column is permitted here. A hard label, logit, Grad-CAM
intensity or detector confidence is not a positive-class probability.

Use separate inputs for each binary task, with one consistent label per group.
Verify external model class order yourself. Distinct tokens for one person cannot
be detected without a correct private identity mapping.

`split` requires at least two participants per class. It produces a new train/val
allocation, discarding any previous split column; it creates no independent test
set. A fresh split requires external retraining before new validation claims.

Model comparison requires the same evaluation sample/group IDs and labels,
evaluation unit, threshold, split and evaluation-role declaration. Do not remove
misclassified samples to equalize files. A validation-only CSV cannot establish
absence of training exposure: audit the complete private manifest first.

## Output handling

Evaluation JSON contains aggregate metrics and an evaluation-set fingerprint, not
raw group tokens. Split outputs contain pseudonymous IDs and paths and remain
private. ROC/calibration CSVs contain curve data. All outputs are ignored by Git;
review before sharing even aggregate results or fingerprints.
