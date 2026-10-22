#!/usr/bin/env python3
"""Optional full-precision MAT inspection (numpy, scipy, h5py required).

The MATLAB comparator remains the release gate. This reads both v5 and v7.3
numeric/cell/struct data; it never accepts unsupported objects as equivalent.
"""
import argparse
import json
from pathlib import Path
import h5py
import numpy as np
import scipy
from scipy.io import loadmat
from scipy import sparse

REQUIRED = ['scores.0.5.mat','peak_regs.mat','wide_peak_regs.mat','perm_ads.mat']

def hdf_value(obj, seen=None):
    seen = set() if seen is None else seen
    if obj.name in seen:
        raise ValueError('cyclic MAT references unsupported')
    seen = seen | {obj.name}
    if isinstance(obj,h5py.Group):
        return {key:hdf_value(value,seen) for key,value in obj.items() if not key.startswith('#')}
    value=obj[()]
    if h5py.check_dtype(ref=obj.dtype):
        result=np.empty(value.shape,dtype=object)
        for idx in np.ndindex(value.shape):
            result[idx]=hdf_value(obj.file[value[idx]],seen) if value[idx] else None
        value=result
    return {'MATLAB_class':obj.attrs.get('MATLAB_class',b''),'value':value}

def load(path):
    if h5py.is_hdf5(path):
        with h5py.File(path,'r') as f: return hdf_value(f)
    return {k:v for k,v in loadmat(path).items() if not k.startswith('__')}

def equal(a,b):
    if type(a) is not type(b): return False
    if isinstance(a,dict):
        return a.keys()==b.keys() and all(equal(a[k],b[k]) for k in a)
    if sparse.issparse(a):
        return a.shape==b.shape and a.dtype==b.dtype and np.array_equal(a.toarray(),b.toarray(),equal_nan=True)
    if isinstance(a,np.ndarray):
        if a.dtype != b.dtype or a.shape != b.shape: return False
        if a.dtype.names:
            return all(equal(a[k],b[k]) for k in a.dtype.names)
        if a.dtype.kind=='O': return all(equal(x,y) for x,y in zip(a.flat,b.flat))
        if a.dtype.kind in 'fc': return np.array_equal(a,b,equal_nan=True)
        return np.array_equal(a,b)
    if isinstance(a,(str,bytes,int,float,np.generic)) or a is None:
        return bool(a==b)
    raise TypeError(f'unsupported MAT object {type(a)}')

def compare_mat(left,right):
    results={}
    for name in REQUIRED + ['orig_stats.mat','gene_stats.mat']:
        a,b=Path(left)/name,Path(right)/name
        if not a.is_file() or not b.is_file():
            results[name]={'status':'missing' if name in REQUIRED else 'unverified_missing_optional'}
            continue
        try: results[name]={'status':'exact_match' if equal(load(a),load(b)) else 'difference'}
        except Exception as exc: results[name]={'status':'unverified_read_error','error':str(exc)}
    return {'files':results,'required_match':all(results[n]['status']=='exact_match' for n in REQUIRED),
            'numpy':np.__version__,'scipy':scipy.__version__,'h5py':h5py.__version__,
            'method':'recursive exact values/dtypes/shapes; MAT metadata and internal reference names excluded; NaNs compare equal'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('baseline');p.add_argument('candidate');a=p.parse_args()
    result=compare_mat(a.baseline,a.candidate)
    print(json.dumps(result,indent=2));raise SystemExit(0 if result['required_match'] else 1)
