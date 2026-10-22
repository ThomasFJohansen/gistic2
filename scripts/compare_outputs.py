#!/usr/bin/env python3
"""Strict scientific text comparison; explicit tolerances only on continuous data.

No row sorting, coordinate tolerance, threshold-call tolerance, or NaN acceptance.
MAT files require the independent MATLAB comparator.
"""
import argparse
import csv
import itertools
import json
import math
from pathlib import Path

SUFFIXES = {'.txt', '.gistic', '.bed'}
REQUIRED = ['scores.gistic', 'all_lesions.conf_90.txt', 'amp_genes.conf_90.txt',
            'del_genes.conf_90.txt', 'all_thresholded.by_genes.txt',
            'sample_seg_counts.txt', 'regions_track.conf_90.bed', 'all_data_by_genes.txt',
            'broad_data_by_genes.txt', 'focal_data_by_genes.txt']

def files(root):
    return {p.name: p for p in Path(root).iterdir()
            if p.is_file() and p.suffix in SUFFIXES and p.name not in {'stdout.txt', 'stderr.txt'}}

def rows(path):
    with Path(path).open(newline='') as handle:
        yield from csv.reader(handle, delimiter='\t')

def continuous(name, row, col):
    return ((name == 'scores.gistic' and row > 0 and col >= 4)
            or (name.startswith('all_lesions.') and row > 0 and col in (5, 6))
            or (name.startswith(('amp_genes.', 'del_genes.')) and row in (1, 2) and col > 0)
            or (name in {'all_data_by_genes.txt', 'broad_data_by_genes.txt', 'focal_data_by_genes.txt'}
                and row > 0 and col >= 3))

def compare(left, right, rtol=0.0, atol=0.0):
    if any(not math.isfinite(x) or x < 0 for x in (rtol, atol)):
        raise ValueError('tolerances must be finite and nonnegative')
    a, b = files(left), files(right)
    errors = []
    changed = 0
    if a.keys() != b.keys():
        errors.append({'file_set': {'missing': sorted(a.keys()-b.keys()), 'extra': sorted(b.keys()-a.keys())}})
    for name in sorted(a.keys() & b.keys()):
        for ri, (ar, br) in enumerate(itertools.zip_longest(rows(a[name]), rows(b[name]))):
            if ar is None or br is None or len(ar) != len(br):
                errors.append(f'{name}:{ri+1}: row/column count differs')
                break
            for ci, (av, bv) in enumerate(zip(ar, br)):
                equal = av == bv
                if continuous(name, ri, ci):
                    try:
                        x, y = float(av), float(bv)
                        equal = math.isfinite(x) and math.isfinite(y) and abs(x-y) <= atol + rtol*max(abs(x), abs(y))
                    except ValueError:
                        equal = False
                    if equal and av != bv:
                        changed += 1
                if not equal:
                    errors.append(f'{name}:{ri+1}:{ci+1}: {av!r} != {bv!r}')
                if len(errors) >= 100:
                    return {'equal': False, 'errors': errors, 'truncated': True}
    return {'equal': not errors, 'files_compared': len(a.keys() & b.keys()),
            'rtol': rtol, 'atol': atol, 'different_numeric_text': changed, 'errors': errors}

def validate(root):
    root = Path(root)
    errors = [f'missing/empty {n}' for n in REQUIRED if not (root/n).is_file() or (root/n).stat().st_size == 0]
    if errors:
        return errors
    try:
        score = iter(rows(root/'scores.gistic'))
        header = next(score)
        if len(header) != 8:
            errors.append('scores.gistic must have 8 columns')
        seen = set()
        for row in score:
            if len(row) != 8 or row[0] not in ('Amp', 'Del'):
                raise ValueError('malformed score row')
            seen.add(row[0])
            if not (0 <= int(row[2]) <= int(row[3])):
                raise ValueError('invalid score coordinates')
            values = [float(x) for x in row[4:]]
            if not all(math.isfinite(x) and x >= 0 for x in values) or values[-1] > 1:
                raise ValueError('invalid score values')
        if seen != {'Amp', 'Del'}:
            errors.append('scores lack amplification or deletion data')
        identities = None
        samples = None
        for name in ('all_data_by_genes.txt', 'broad_data_by_genes.txt', 'focal_data_by_genes.txt'):
            table = iter(rows(root/name))
            hdr = next(table)
            ids = []
            for row in table:
                if len(row) != len(hdr):
                    raise ValueError(f'{name}: incomplete row')
                ids.append(row[:3])
            if not ids:
                raise ValueError(f'{name}: no genes')
            if identities is not None and (ids != identities or hdr != samples):
                errors.append(f'{name}: gene/sample identities differ across gene tables (possibly truncated)')
            identities, samples = ids, hdr
    except (ValueError, StopIteration, IndexError) as exc:
        errors.append(str(exc) or 'empty table')
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('baseline', type=Path)
    parser.add_argument('candidate', type=Path)
    parser.add_argument('--rtol', type=float, default=0)
    parser.add_argument('--atol', type=float, default=0)
    args = parser.parse_args()
    result = compare(args.baseline, args.candidate, args.rtol, args.atol)
    result['baseline_validation'] = validate(args.baseline)
    result['candidate_validation'] = validate(args.candidate)
    result['equal'] &= not result['baseline_validation'] and not result['candidate_validation']
    print(json.dumps(result, indent=2))
    return 0 if result['equal'] else 1

if __name__ == '__main__':
    raise SystemExit(main())
