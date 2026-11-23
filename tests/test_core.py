import copy
import tempfile
import unittest
from pathlib import Path
from facial_analysis.core import (metrics,auc,aggregate,split_groups,validate,
                                  bootstrap_ci,ppv_scenarios,safe_path)
from facial_analysis.cli import audit_images,main


def row(s,g,y,split='val',p=.5):
    return dict(sample_id='sample_'+s,group_id='group_'+g,label=str(y),
                probability=str(p),split=split)


class StatisticalTests(unittest.TestCase):
    def test_confusion_metrics(self):
        m=metrics([1,1,0,0],[.9,.2,.7,.1])
        self.assertEqual([m[k] for k in ['tp','fn','fp','tn']],[1,1,1,1])
        for key in ['accuracy','sensitivity','specificity','precision','f1']:
            self.assertEqual(m[key],.5)
    def test_auc_ties_and_ranking(self):
        self.assertEqual(auc([0,1],[.5,.5]),.5)
        self.assertEqual(auc([0,0,1,1],[.1,.4,.35,.8]),.75)
        self.assertEqual(auc([0,1],[.9,.1]),0)
    def test_auc_no_second_class(self):
        self.assertIsNone(auc([1,1],[.2,.8]))
    def test_undefined_ppv_not_zero(self):
        self.assertIsNone(metrics([0,1],[.1,.2])['ppv'])
    def test_invalid_score(self):
        with self.assertRaises(ValueError):metrics([0,1],[.1,float('nan')])
    def test_patient_aggregation_equal_weight(self):
        rows=[row('a','a',1,p=.2),row('b','a',1,p=.8),row('c','b',0,p=.1)]
        a=aggregate(validate(rows,True))
        self.assertEqual(len(a),2)
        self.assertEqual(a[0]['probability'],.5)
    def test_leakage_rejected(self):
        rows=[row('a','a',1,'train'),row('b','a',1,'val')]
        with self.assertRaises(ValueError):validate(rows,True)
    def test_conflicting_labels_rejected(self):
        with self.assertRaises(ValueError):validate([row('a','a',0),row('b','a',1)],True)
    def test_duplicate_sample_rejected(self):
        with self.assertRaises(ValueError):validate([row('a','a',0),row('a','b',1)],True)
    def test_partition_group_integrity(self):
        rows=[]
        for y in (0,1):
            for i in range(6):
                for j in range(2):
                    rows.append(dict(sample_id=f'sample_{y}{i}{j}',group_id=f'group_{y}{i}',
                                     image_path=f'images/sample_{y}{i}{j}.png',label=str(y)))
        a=split_groups(rows);b=split_groups(rows)
        self.assertEqual(a,b)
        self.assertFalse({r['group_id'] for r in a if r['split']=='train'} &
                         {r['group_id'] for r in a if r['split']=='val'})
        for s in ('train','val'):
            self.assertEqual({r['label'] for r in a if r['split']==s},{'0','1'})
    def test_bootstrap_deterministic(self):
        rs=[dict(group_id=f'group_{y}{i}',label=y,probability=.15+.2*i+.2*y) for y in (0,1) for i in range(3)]
        a=bootstrap_ci(rs,30);b=bootstrap_ci(rs,30)
        self.assertEqual(a,b)
        self.assertEqual(a['intervals']['auc']['valid_replicates'],30)
    def test_small_group_ci_not_estimated(self):
        a=bootstrap_ci([dict(group_id='group_a',label=0,probability=.2)],30)
        self.assertEqual(a['method'],'not_estimated')
    def test_ppv_scenario(self):
        a=ppv_scenarios(1,[.99],[.01])[0]
        self.assertAlmostEqual(a['theoretical_ppv'],.01/(.01+.01*.99))
        self.assertEqual(ppv_scenarios(.9,[1],[.001])[0]['theoretical_ppv'],1)
    def test_paths(self):
        for p in ['../secret.png','/secret.png','C:\\secret.png']:
            with self.assertRaises(ValueError):safe_path('.',p)
    def test_byte_duplicate_across_partitions(self):
        with tempfile.TemporaryDirectory() as td:
            Path(td,'a').write_bytes(b'same');Path(td,'b').write_bytes(b'same')
            with self.assertRaises(ValueError):audit_images([
                dict(image_path='a',split='train'),dict(image_path='b',split='val')],td)


if __name__=='__main__':unittest.main()
