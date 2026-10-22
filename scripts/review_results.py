#!/usr/bin/env python3
"""Re-evaluate retained outputs without rerunning GISTIC or altering raw results."""
import argparse
import json
from pathlib import Path
from compare_outputs import compare, validate
from regression import sha

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('matrix',type=Path)
p.add_argument('--baseline',type=Path)
p.add_argument('--mat',action='store_true')
p.add_argument('--note',default='Post-run scientific review with current comparator')
a=p.parse_args()
raw=json.loads((a.matrix/'summary.json').read_text())
reference=a.baseline
review={'note':a.note,'raw_summary_sha256':sha(a.matrix/'summary.json'),
        'comparator_sha256':sha(Path(__file__).with_name('compare_outputs.py')),'runs':[]}
if a.mat:
    from compare_mat_outputs import compare_mat
    review['mat_comparator_sha256']=sha(Path(__file__).with_name('compare_mat_outputs.py'))
for r in raw:
    out=a.matrix/f"{r['repeat']:02d}-{r['case']}"/'outputs'
    validation=validate(out)
    entry={k:r[k] for k in ('case','repeat','returncode','timeout','wall_seconds','cpu_seconds')}
    entry['validation_errors']=validation
    entry['output_hashes_unchanged']=all((out/n).is_file() and sha(out/n)==h for n,h in r['output_sha256'].items())
    complete=r['returncode']==0 and not r['timeout'] and not validation and entry['output_hashes_unchanged']
    if complete:
        if reference is None: reference=out
        entry['text_comparison']=compare(reference,out)
        entry['status']='match' if entry['text_comparison']['equal'] else 'difference'
        if a.mat:
            entry['mat_comparison']=compare_mat(reference,out)
            if not entry['mat_comparison']['required_match']: entry['status']='difference_or_unverified_mat'
    else:
        entry['status']='failed'
    review['runs'].append(entry)
review['baseline']=str(reference)
path=a.matrix/'review.json'
if path.exists(): raise FileExistsError(path)
path.write_text(json.dumps(review,indent=2)+'\n')
print(json.dumps([{k:r[k] for k in ('case','repeat','status','wall_seconds','cpu_seconds')} for r in review['runs']],indent=2))
raise SystemExit(0 if all(r['status']=='match' for r in review['runs']) else 1)
