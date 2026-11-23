# Implemented analysis definitions

This document defines data partitioning, performance metrics and statistical
procedures implemented by the analysis package. All performance calculations
use the supplied labels and positive-class probabilities.

## Partitioning and checks

`split` groups images by token, checks consistent labels and shuffles sorted group
lists separately within each class with a seeded Python random generator.
Validation group count is round-half-up of fraction times group count, bounded to
keep both train and val per class. All photos follow their group. A new allocation requires model training on the designated training partition
before performance is evaluated on the corresponding validation partition.

`audit` detects participant overlap in the supplied full manifest. With a data
root it also checks exact SHA256 image-byte duplicates across partitions. It
cannot identify near-duplicates, siblings or multiple tokens for the same person.
No face-recognition matching is used.

## Binary metrics

A probability >= the predeclared threshold (default 0.5) is positive. Undefined
ratios are `null`. All values use the same label/probability records:

- Sensitivity = TP/(TP+FN)
- Specificity = TN/(TN+FP)
- Precision and validation-set PPV = TP/(TP+FP)
- NPV = TN/(TN+FN)
- Accuracy = (TP+TN)/N
- F1 = 2TP/(2TP+FP+FN)
- Brier score = mean squared difference between probability and binary label

ROC processes unique observed probability thresholds together for ties; AUC is
trapezoidal integration. AUC is undefined with one class. ROC and AUC require continuous prediction scores and both class labels.

## Participant aggregation and confidence intervals

The explicit implementation rule is arithmetic mean positive probability across
all photos of one participant. Every participant contributes once. Label image-level and participant-level results separately.

The 95% percentile bootstrap samples participants with replacement within each
class, preserving class counts and carrying one aggregate score for every sampled
participant. Quantiles use linear interpolation at 2.5% and 97.5%. This is not a
model refit. It needs at least two participants per class, reports valid replicate
counts and does not estimate image-level intervals. Two participants is a
computational minimum, not adequate precision evidence.

Perfect observed scores can produce degenerate bootstrap intervals. They do not
establish zero population uncertainty. The intervals condition on predictions
and chosen class counts, not model-selection uncertainty or population prevalence.
They do not correct image-source confounding, validation reuse or leakage.

## Calibration

Ten equal-width bins and Brier score are descriptive. Empty bins have null means
and fractions. Small-sample calibration is unstable. No recalibration model is
fitted on evaluation data and no calibration slope or clinical validity is claimed.

## Hypothetical PPV

`PPV = Se*p / (Se*p + (1-Sp)*(1-p))`.

Explicitly state Se, Sp and assumed target prevalence p. These scenarios assume
Se/Sp transport unchanged; they are not clinical observations. Prevalence refers
to the classifier's positive outcome, not automatically a specific syndrome.
With Sp=1 and p>0, the formula returns PPV=1, without proving perfect screening
utility. Zero false positives in a small sample does not establish Sp=1.

## Figures

Python/matplotlib draws directly from prediction-derived metrics/curves. SVG/PDF
use editable text where supported; PNG is 300 dpi. Synthetic runs are labeled.
Curve coordinates, counts and intervals are generated from the supplied input records.
