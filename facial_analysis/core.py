"""Dependency-free binary evaluation and participant-disjoint partitioning."""
import csv
import json
import math
import random
import re
from collections import defaultdict
from pathlib import Path, PurePosixPath


def read_csv(path):
    with open(path, newline='', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or len(reader.fieldnames) != len(set(reader.fieldnames)):
            raise ValueError('CSV must have unique named columns.')
        rows = list(reader)
    if not rows:
        raise ValueError('Empty CSV.')
    return rows


def write_csv(path, rows, fields=None):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows and fields is None:
        raise ValueError('Specify fields for an empty output.')
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields or list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def safe_path(root, relative):
    """Accept portable paths confined to a private data root."""
    p = PurePosixPath(relative)
    if p.is_absolute() or '..' in p.parts or '\\' in relative or ':' in relative:
        raise ValueError('Image and mask paths must be relative POSIX paths.')
    root = Path(root).resolve()
    dest = (root / str(p)).resolve()
    if dest != root and root not in dest.parents:
        raise ValueError('Path escapes data root.')
    return dest


def validate(rows, predictions=False, require_split=True):
    seen = set()
    labels = {}
    partitions = defaultdict(set)
    for r in rows:
        for key, prefix in [('sample_id', 'sample'), ('group_id', 'group')]:
            if not re.fullmatch(prefix + r'_[a-z0-9]+', r.get(key, '')):
                raise ValueError('Use randomly assigned opaque sample_*/group_* tokens.')
        if r['sample_id'] in seen:
            raise ValueError('Duplicate sample_id.')
        seen.add(r['sample_id'])
        if str(r.get('label')) not in ('0', '1'):
            raise ValueError('label must be 0 or 1; 1 denotes the positive outcome.')
        y = int(r['label'])
        g = r['group_id']
        if g in labels and labels[g] != y:
            raise ValueError('A group has conflicting labels within a binary task.')
        labels[g] = y
        split = r.get('split', '')
        if require_split and split not in ('train', 'val', 'test'):
            raise ValueError('split must be train, val or test.')
        if split:
            partitions[g].add(split)
        if predictions:
            q = float(r.get('probability', 'nan'))
            if not math.isfinite(q) or not 0 <= q <= 1:
                raise ValueError('probability must be finite and in [0,1].')
        else:
            safe_path('.', r.get('image_path', ''))
            if not r.get('image_path'):
                raise ValueError('image_path is required.')
    if any(len(s) > 1 for s in partitions.values()):
        raise ValueError('Participant overlap across partitions detected.')
    return rows


def split_groups(rows, val_fraction=.3, seed=20261123):
    """Fresh class-stratified group split; ignores old allocation explicitly."""
    if not 0 < val_fraction < 1:
        raise ValueError('val_fraction must lie strictly between 0 and 1.')
    fresh = [{k: v for k, v in r.items() if k != 'split'} for r in rows]
    validate(fresh, require_split=False)
    classes = defaultdict(set)
    for r in fresh:
        classes[int(r['label'])].add(r['group_id'])
    if set(classes) != {0, 1} or any(len(g) < 2 for g in classes.values()):
        raise ValueError('Need at least two participants in each class.')
    rng = random.Random(seed)
    val = set()
    for y in (0, 1):
        groups = sorted(classes[y])
        rng.shuffle(groups)
        k = max(1, min(len(groups)-1, int(len(groups)*val_fraction + .5)))
        val.update(groups[:k])
    result = [dict(r, split='val' if r['group_id'] in val else 'train') for r in fresh]
    validate(result)
    return result


def partition_summary(rows):
    result = []
    for s in ('train', 'val', 'test'):
        for y in (0, 1):
            subset = [r for r in rows if r['split'] == s and int(r['label']) == y]
            if subset:
                result.append(dict(split=s, label=y, images=len(subset),
                                   participants=len({r['group_id'] for r in subset})))
    return result


def roc_points(y, scores):
    pos = sum(y)
    neg = len(y)-pos
    if not pos or not neg:
        return []
    grouped = defaultdict(lambda: [0, 0])
    for a, b in zip(y, scores):
        grouped[b][int(a)] += 1
    points = [dict(threshold=None, fpr=0.0, tpr=0.0)]
    tp = fp = 0
    for threshold in sorted(grouped, reverse=True):
        n0, n1 = grouped[threshold]
        fp += n0
        tp += n1
        points.append(dict(threshold=threshold, fpr=fp/neg, tpr=tp/pos))
    return points


def auc(y, scores):
    pts = roc_points(y, scores)
    if not pts:
        return None
    return sum((b['fpr']-a['fpr'])*(a['tpr']+b['tpr'])/2
               for a, b in zip(pts, pts[1:]))


def metrics(y, scores, threshold=.5):
    if not y or len(y) != len(scores) or not 0 <= threshold <= 1:
        raise ValueError('Invalid labels, scores or threshold.')
    if any(v not in (0, 1) for v in y) or any(not math.isfinite(q) or not 0 <= q <= 1 for q in scores):
        raise ValueError('Invalid binary label or probability.')
    pred = [int(p >= threshold) for p in scores]
    tp = sum(a == b == 1 for a, b in zip(y, pred))
    tn = sum(a == b == 0 for a, b in zip(y, pred))
    fp = sum(a == 0 and b == 1 for a, b in zip(y, pred))
    fn = sum(a == 1 and b == 0 for a, b in zip(y, pred))
    def div(a, b):
        return a/b if b else None
    return dict(n=len(y), tp=tp, fn=fn, fp=fp, tn=tn, threshold=threshold,
                accuracy=(tp+tn)/len(y), precision=div(tp, tp+fp),
                sensitivity=div(tp, tp+fn), specificity=div(tn, tn+fp),
                ppv=div(tp, tp+fp), npv=div(tn, tn+fn),
                f1=div(2*tp, 2*tp+fp+fn), auc=auc(y, scores),
                brier=sum((q-a)**2 for a, q in zip(y, scores))/len(y))


def aggregate(rows):
    """Arithmetic mean of positive-class image probabilities per participant."""
    by = defaultdict(list)
    for r in rows:
        by[r['group_id']].append(r)
    return [dict(group_id=g, label=int(rs[0]['label']),
                 probability=sum(float(r['probability']) for r in rs)/len(rs),
                 images=len(rs)) for g, rs in sorted(by.items())]


def bootstrap_ci(rows, repeats=2000, seed=20261123, threshold=.5):
    """Class-stratified participant bootstrap on mean participant scores."""
    if repeats < 0:
        raise ValueError('repeats must be nonnegative.')
    by = {y: [r for r in rows if int(r['label']) == y] for y in (0, 1)}
    if not repeats or any(len(rs) < 2 for rs in by.values()):
        return {'method': 'not_estimated', 'reason': 'Disabled or fewer than two participants per class.'}
    keys = ['accuracy', 'sensitivity', 'specificity', 'ppv', 'npv', 'f1', 'auc', 'brier']
    vals = {k: [] for k in keys}
    rng = random.Random(seed)
    for _ in range(repeats):
        sample = [rng.choice(by[y]) for y in (0, 1) for _ in by[y]]
        m = metrics([int(r['label']) for r in sample], [float(r['probability']) for r in sample], threshold)
        for k in keys:
            if m[k] is not None:
                vals[k].append(m[k])
    def quantile(a, q):
        a = sorted(a)
        i = (len(a)-1)*q
        lo = int(i)
        return a[lo]+(a[min(lo+1,len(a)-1)]-a[lo])*(i-lo)
    result = {'method': 'class_stratified_participant_percentile_bootstrap', 'repeats': repeats,
              'seed': seed, 'level': .95, 'warning': 'Conditional on predictions and fixed class counts; excludes model-selection uncertainty. Perfect scores may produce degenerate intervals.'}
    result['intervals'] = {k: dict(low=quantile(v,.025), high=quantile(v,.975), valid_replicates=len(v))
                           for k,v in vals.items() if v}
    return result


def calibration(y, scores, bins=10):
    out = []
    for i in range(bins):
        ix = [j for j,p in enumerate(scores) if min(int(p*bins),bins-1) == i]
        out.append(dict(bin=i, count=len(ix),
                        mean_probability=sum(scores[j] for j in ix)/len(ix) if ix else None,
                        positive_fraction=sum(y[j] for j in ix)/len(ix) if ix else None))
    return out


def ppv_scenarios(sensitivity, specificities, prevalences):
    if not 0 <= sensitivity <= 1 or any(not 0 <= x <= 1 for x in specificities) or any(not 0 < p < 1 for p in prevalences):
        raise ValueError('Invalid scenario inputs.')
    out = []
    for p in prevalences:
        for s in specificities:
            den = sensitivity*p+(1-s)*(1-p)
            out.append(dict(assumed_prevalence=p, sensitivity=sensitivity,
                            assumed_specificity=s, theoretical_ppv=sensitivity*p/den if den else None,
                            status='hypothetical_scenario_not_clinical_performance'))
    return out
