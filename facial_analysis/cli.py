"""Public command-line interface. Private input/output files remain local."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from .core import (read_csv, write_csv, write_json, validate, split_groups,
                   partition_summary, aggregate, metrics, bootstrap_ci, roc_points,
                   calibration, ppv_scenarios, safe_path)


def input_rows(path, predictions=False, require_split=True):
    rows=read_csv(path)
    allowed={'sample_id','group_id','label','split','data_kind'}
    allowed.add('probability' if predictions else 'image_path')
    if set(rows[0])-allowed:
        raise ValueError('Unexpected CSV columns; remove clinical or identifying fields.')
    if any(r.get('data_kind','') not in ('','synthetic','private') for r in rows):
        raise ValueError('data_kind must be synthetic or private when supplied.')
    if not require_split:
        rows=[{k:v for k,v in r.items() if k!='split'} for r in rows]
    return validate(rows,predictions,require_split)


def audit_images(rows,root):
    """Fail if identical file bytes occur in different partitions."""
    hashes={}
    for r in rows:
        p=safe_path(root,r['image_path'])
        if not p.is_file():
            raise ValueError('An image is unavailable under the supplied data root.')
        h=hashlib.sha256(p.read_bytes()).hexdigest()
        if h in hashes and hashes[h]!=r['split']:
            raise ValueError('Identical image bytes occur in different partitions.')
        hashes[h]=r['split']
    return {'images_checked':len(rows),'unique_file_hashes':len(hashes),'cross_partition_duplicates':0,
            'limitation':'Does not identify near-duplicates or multiple anonymous tokens for one person.'}


def evaluate(args):
    rows=input_rows(args.predictions,True)
    subset=[r for r in rows if r['split']==args.split]
    if not subset:
        raise ValueError('Requested evaluation partition is empty.')
    patients=aggregate(subset)
    units=patients if args.unit=='participant' else subset
    y=[int(r['label']) for r in units];scores=[float(r['probability']) for r in units]
    if set(y)!={0,1}:
        raise ValueError('Both classes are required for evaluation.')
    m=metrics(y,scores,args.threshold)
    # Hash the evaluation identities/labels, without publishing those identities.
    identity='\n'.join(sorted(f"{r['sample_id']}|{r['group_id']}|{r['label']}" for r in subset))
    synthetic=all(r.get('data_kind')=='synthetic' for r in rows)
    report={'software':'facial-analysis 0.1.0','data_kind':'synthetic' if synthetic else 'private',
            'split':args.split,'unit':args.unit,'threshold':args.threshold,
            'evaluation_set_sha256':hashlib.sha256(identity.encode()).hexdigest(),
            'images':len(subset),'participants':len(patients),
            'aggregation':'mean positive probability per participant' if args.unit=='participant' else 'none',
            'metrics':m,'evaluation_role':args.role,
            'interpretation':'Internal developmental validation; model-selection bias is not removed.' if args.role=='developmental' else 'Independence is an investigator-supplied assertion, not established by this software.'}
    report['confidence_intervals']=bootstrap_ci(patients,args.bootstrap,args.seed,args.threshold) if args.unit=='participant' else {
        'method':'not_estimated','reason':'Use participant-level evaluation; images may be correlated.'}
    out=Path(args.output)
    write_json(out/'metrics.json',report)
    roc=roc_points(y,scores);cal=calibration(y,scores)
    write_csv(out/'roc.csv',roc);write_csv(out/'calibration.csv',cal)
    write_csv(out/'confusion_matrix.csv',[{k:m[k] for k in ['tp','fn','fp','tn','n','threshold']}])
    # Per-participant/per-image outputs stay private and are intentionally not copied.
    if args.plots:
        from .plots import evaluation_plots
        evaluation_plots(out,roc,m,cal,synthetic)
    print(json.dumps({'images':len(subset),'participants':len(patients),'metrics':m},allow_nan=False))


def main(argv=None):
    p=argparse.ArgumentParser(description='Data partitioning and statistical evaluation of binary classifier predictions.')
    sub=p.add_subparsers(dest='command',required=True)
    s=sub.add_parser('split',help='Create a NEW patient-disjoint, class-stratified split.')
    s.add_argument('--manifest',required=True);s.add_argument('--output',required=True)
    s.add_argument('--val-fraction',type=float,default=.3);s.add_argument('--seed',type=int,default=20261123)
    a=sub.add_parser('audit',help='Check participant leakage and exact image-byte duplicates.')
    a.add_argument('--manifest',required=True);a.add_argument('--data-root');a.add_argument('--output',required=True)
    e=sub.add_parser('evaluate',help='Evaluate real probability outputs; never infer predictions from aggregate metrics.')
    e.add_argument('--predictions',required=True);e.add_argument('--output',required=True)
    e.add_argument('--split',choices=['val','test'],default='val')
    e.add_argument('--unit',choices=['participant','image'],default='participant')
    e.add_argument('--threshold',type=float,default=.5);e.add_argument('--bootstrap',type=int,default=2000)
    e.add_argument('--seed',type=int,default=20261123);e.add_argument('--plots',action='store_true')
    e.add_argument('--role',choices=['developmental','independent'],default='developmental')
    q=sub.add_parser('ppv',help='Explicitly hypothetical prevalence scenarios.')
    q.add_argument('--sensitivity',type=float,required=True)
    q.add_argument('--specificities',type=float,nargs='+',required=True)
    q.add_argument('--prevalences',type=float,nargs='+',required=True);q.add_argument('--output',required=True)
    c=sub.add_parser('compare',help='Compare like-for-like evaluation reports.')
    c.add_argument('--reports',nargs='+',required=True,help='Pairs NAME=relative/path/metrics.json')
    c.add_argument('--output',required=True)
    args=p.parse_args(argv)
    try:
        if args.command=='split':
            rows=input_rows(args.manifest,require_split=False)
            result=split_groups(rows,args.val_fraction,args.seed)
            write_csv(args.output,result)
            write_json(str(args.output)+'.summary.json',{'seed':args.seed,'new_partition':True,
                      'method':'class_stratified_random_participant_split','counts':partition_summary(result)})
        elif args.command=='audit':
            rows=input_rows(args.manifest)
            result={'patient_disjoint':True,'counts':partition_summary(rows)}
            if args.data_root:result['image_audit']=audit_images(rows,args.data_root)
            else:result['image_audit']='not_performed_without_data_root'
            write_json(args.output,result)
        elif args.command=='evaluate':evaluate(args)
        elif args.command=='ppv':
            write_csv(args.output,ppv_scenarios(args.sensitivity,args.specificities,args.prevalences))
        elif args.command=='compare':
            pairs=[]
            for spec in args.reports:
                name,path=spec.split('=',1)
                if name not in ('ResNet18','ResNet34','ResNet50'):
                    raise ValueError('Use generic model names ResNet18/34/50.')
                pairs.append((name,json.loads(Path(path).read_text())))
            if len({name for name,_ in pairs})!=len(pairs):
                raise ValueError('Duplicate model name.')
            signatures={(r['evaluation_set_sha256'],r['unit'],r['threshold'],r['split'],r['evaluation_role']) for _,r in pairs}
            if len(signatures)!=1:
                raise ValueError('Reports do not use identical samples, labels, units, partitions, thresholds and evaluation roles.')
            rows=[dict(model=n,**r['metrics']) for n,r in pairs]
            write_csv(Path(args.output)/'comparison.csv',rows)
            from .plots import comparison
            comparison(args.output,pairs)
    except (ValueError,KeyError,OSError,TypeError,OverflowError,ModuleNotFoundError) as exc:
        # Avoid printing private file paths or CSV values in automatic tracebacks.
        print('Analysis failed: check input schema, class labels, probability ranges, participant overlap, '
              'comparison compatibility, file availability and optional dependencies. '
              'Input values and private paths are omitted from this message.',file=sys.stderr)
        return 2
    return 0
