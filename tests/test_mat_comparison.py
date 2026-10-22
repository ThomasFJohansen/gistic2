import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
AVAILABLE=all(importlib.util.find_spec(m) for m in ('numpy','scipy','h5py'))

@unittest.skipUnless(AVAILABLE,'optional numpy/scipy/h5py not installed')
class MatComparison(unittest.TestCase):
    def test_full_precision_change_not_hidden_by_rounding(self):
        import numpy as np
        from compare_mat_outputs import equal
        a=np.array([0.123456789]);b=np.array([0.123456788])
        self.assertEqual(f'{a[0]:.6f}',f'{b[0]:.6f}')
        self.assertFalse(equal(a,b))

    def test_struct_coordinate_change(self):
        import numpy as np
        from compare_mat_outputs import equal
        a=np.array([(20,0.001)],dtype=[('peak_start','i8'),('q','f8')]);b=a.copy()
        b['peak_start']=21
        self.assertFalse(equal(a,b))

    def test_hdf_reference_names_do_not_change_values(self):
        import h5py
        import numpy as np
        from compare_mat_outputs import equal,load
        with tempfile.TemporaryDirectory() as tmp:
            paths=[Path(tmp)/'a.mat',Path(tmp)/'b.mat']
            for path,name in zip(paths,('internal_a','internal_z')):
                with h5py.File(path,'w') as f:
                    group=f.create_group('#refs#')
                    target=group.create_dataset(name,data=np.array([1.,2.]))
                    root=f.create_dataset('scores',(1,),dtype=h5py.ref_dtype)
                    root[0]=target.ref
            self.assertTrue(equal(load(paths[0]),load(paths[1])))
            with h5py.File(paths[1],'a') as f: f['#refs#/internal_z'][1]=3.
            self.assertFalse(equal(load(paths[0]),load(paths[1])))
