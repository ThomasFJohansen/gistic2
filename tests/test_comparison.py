from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from compare_outputs import compare,validate,REQUIRED

class Comparison(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.a=Path(self.tmp.name)/'a'; self.b=Path(self.tmp.name)/'b'
        self.a.mkdir(); self.b.mkdir()
        self.score='Type\tChromosome\tStart\tEnd\t-log10(q)\tG-score\tAverage amplitude\tFrequency\nAmp\t1\t10\t20\t2\t0.2\t0.1\t0.5\nDel\t1\t21\t25\t3\t0.3\t0.2\t0.4\n'
        for root in (self.a,self.b):
            for name in REQUIRED: (root/name).write_text('header\nvalue\n')
            (root/'scores.gistic').write_text(self.score)
            for kind in ('all','broad','focal'):
                (root/f'{kind}_data_by_genes.txt').write_text('Gene\tID\tCytoband\tsample\nABC\t1\t1p1\t0.2\nDEF\t2\t1p2\t0.3\n')
    def test_same(self):
        self.assertTrue(compare(self.a,self.b)['equal']); self.assertEqual(validate(self.a),[])
    def test_missing(self):
        (self.b/'scores.gistic').unlink(); self.assertFalse(compare(self.a,self.b)['equal'])
    def test_coordinates_strict(self):
        (self.b/'scores.gistic').write_text(self.score.replace('\t10\t','\t11\t'))
        self.assertFalse(compare(self.a,self.b,100,100)['equal'])
    def test_continuous_tolerance_explicit(self):
        (self.b/'scores.gistic').write_text(self.score.replace('\t0.2\t','\t0.20000000001\t'))
        self.assertFalse(compare(self.a,self.b)['equal'])
        self.assertTrue(compare(self.a,self.b,0,1e-9)['equal'])
    def test_large_change_rejected(self):
        (self.b/'scores.gistic').write_text(self.score.replace('\t0.2\t','\t0.3\t'))
        self.assertFalse(compare(self.a,self.b,0,1e-9)['equal'])
    def test_nonfinite_rejected_even_identical(self):
        for root in (self.a,self.b): (root/'scores.gistic').write_text(self.score.replace('\t0.2\t','\tnan\t'))
        self.assertFalse(compare(self.a,self.b)['equal']); self.assertTrue(validate(self.a))
    def test_calls_strict(self):
        (self.b/'all_thresholded.by_genes.txt').write_text('header\n2\n')
        self.assertFalse(compare(self.a,self.b,100,100)['equal'])
    def test_truncated_gene_table(self):
        p=self.b/'focal_data_by_genes.txt'; p.write_text('\n'.join(p.read_text().splitlines()[:2])+'\n')
        self.assertTrue(validate(self.b)); self.assertFalse(compare(self.a,self.b)['equal'])
    def test_invalid_tolerance(self):
        for v in (-1,float('nan'),float('inf')):
            with self.assertRaises(ValueError): compare(self.a,self.b,atol=v)

    def test_padded_gene_summary_cells(self):
        for root in (self.a,self.b):
            (root/'amp_genes.conf_90.txt').write_text('header\tpeak\t\nq value\t0.1\t\nresidual q value\t0.2\t\n')
        self.assertTrue(compare(self.a,self.b)['equal'])

    def test_blank_numeric_gene_data_rejected(self):
        for root in (self.a,self.b):
            p=root/'focal_data_by_genes.txt'
            p.write_text(p.read_text().replace('\t0.2\n','\t\n'))
        self.assertFalse(compare(self.a,self.b)['equal'])
