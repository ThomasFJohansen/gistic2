# Regression and compatibility testing

## Portable checks

```bash
bash -n support/gistic2 support/run_gistic_example scripts/*.sh
python3 -m unittest discover -s tests -v
```

CI runs these on Ubuntu 24.04. They exercise argument boundaries, empty arguments,
paths containing spaces, injection strings, library isolation, ABI errors,
exit propagation, absent taskset, and a restricted allowed CPU set. They also
check that numerical tolerance cannot hide coordinate/call changes, nonfinite
numbers, missing files, or truncated gene tables. They do not execute MATLAB.

## Original release versus launcher modes

Use an official GISTIC 2.0.23 executable that requires Runtime 8.3, **not** the
stale executable in `support/`. Supply the direct R2014a Runtime root. The original
launcher must be in a working original installation with its expected
`MATLAB_Compiler_Runtime/v83` layout. Preserve that installation.

```bash
python3 scripts/regression.py \
  --runtime /absolute/MATLAB_Compiler_Runtime/v83 \
  --executable /absolute/original/gp_gistic2_from_seg \
  --original-launcher /absolute/original/gistic2 \
  --output /absolute/new-matrix \
  --cases original off threads affinity single --experimental-mkl --repeats 3
```

All runs are serial and use the same executable, official example inputs, options,
CPU allocation and private fresh MCR cache. The harness clears inherited
thread/dispatch and library overrides, records hashes and selected environment,
wall/child-CPU time, timeout/exit code and outputs. Extra OS compatibility
libraries can be provided through `GISTIC_EXTRA_LIBRARY_PATH`. Do not execute
other numerical benchmarks concurrently. Use local scratch for active outputs,
then archive them when complete; do not let synchronization copy partially
written outputs. Run time includes Runtime extraction/startup. OS page caches,
virtual-host contention and case ordering remain potential confounders.

Without `--baseline`, the first complete run is a **within-environment reference**,
not an independent scientific ground truth. The harness refuses incomplete
external baselines and requires the official example's confidence-90 filenames.
`--args-json` accepts an exact array of CLI strings excluding `-b`; the runner
provides a new output directory for each case. Custom configurations with other
confidence levels/prefixes/output settings require a corresponding output schema;
the default completeness validator intentionally fails those rather than claiming
success. The command runner does not edit inputs or repair scientific failures.

The full text comparison requires identical file sets, row order, sample/gene
identities, coordinates, peak calls and thresholded calls. Floating-point fields
are compared numerically with **zero** default tolerance; all other cells are
exact text. Optional `--atol`/`--rtol` in `compare_outputs.py` apply only to the
explicit continuous fields and report changed numerical text. A nonzero tolerance
must be justified for the particular rebuild; it is never a fix for changed
peaks, q-value significance decisions, genes, or coordinates. Padding cells in
gene summary tables may be empty in both outputs. Nonfinite numerical entries
are rejected. No sorting, gene deletion, clipping or replacement of NaN is done.

```bash
python3 scripts/compare_outputs.py /baseline/outputs /candidate/outputs
```

## Full-precision outputs

Text tables are rounded. Also inspect scores, peak regions, wide peaks and null
model output. Optional Python readers support v5 and v7.3 MAT files:

```bash
python3 -m venv /absolute/mat-comparison-env
/absolute/mat-comparison-env/bin/pip install -r tests/requirements-mat.txt
/absolute/mat-comparison-env/bin/python scripts/compare_mat_outputs.py \
  /baseline/outputs /candidate/outputs
```

This comparison recursively checks exact shapes, types and values, including
peak coordinates and q-values stored in the region structures. It excludes MAT
headers, internal reference identifiers and transient path-containing inputs.
Matching NaNs in MAT structs compare equal, so this is an equivalence check,
not a proof of finite scientific values; the text validator separately checks
finite scores. Unsupported objects/read errors are unverified, not passed.

On a licensed MATLAB installation, the release gate is also:

```matlab
addpath('/absolute/gistic2/tests/matlab');
compare_mat_outputs('/baseline/outputs','/candidate/outputs');
```

Both comparators require `scores.0.5.mat`, `peak_regs.mat`, `wide_peak_regs.mat`,
and `perm_ads.mat`. This example uses broad cutoff 0.5. The original executable's
default example does not produce `orig_stats.mat` or `gene_stats.mat`; those are
explicitly reported unverified. For deeper null-model/p/q checks run a matched
baseline/candidate with `-savedata 1 -genepattern 0` (and sufficient disk), then
compare those optional files as well. The existing MATLAB source conditionally
writes them. `gistic_inputs.mat` contains environment/path metadata and is not a
numerical baseline; plot byte equality is not required across MATLAB versions.

## Independently published GenePattern tables

```bash
python3 scripts/fetch_reference.py /absolute/new-genepattern-reference
python3 scripts/regression.py \
  --runtime /absolute/MATLAB_Compiler_Runtime/v83 \
  --executable /absolute/original/gp_gistic2_from_seg \
  --output /absolute/new-genepattern-test --profile genepattern \
  --baseline /absolute/new-genepattern-reference --cases off single --repeats 1
```

The manifest pins GenePattern commit
`9455555051a59a2aa095bc84834227622b13bec1` and verifies Git blob SHA-1 and size for
every retrieved scientific table. Only the known `segmentationfile.` filename
prefix is removed. The external reference MAT download returned HTTP 503 during this investigation.
The four text inputs match the published Git blobs; equivalence of the separately
hosted Human_Hg16.mat and the local hg16.mat is unverified unless the complete
output comparison succeeds. This suite has join size 4, arm peeling off and broad analysis
off; the standalone official example uses different settings. Do not compare
those profiles as though they were equivalent. Check the original
[GenePattern test specification](https://github.com/genepattern/GISTIC_2.0/blob/9455555051a59a2aa095bc84834227622b13bec1/gpunit/example/example.yml)
and input/reference hashes when investigating differences.

## Acceptance criteria and remaining gates

A launcher mode passes this example only when it completes, produces complete
outputs, and matches the chosen baseline. Repeated runs must agree. A modern
release additionally requires a successful licensed build and source execution,
a matching Runtime deployment, full-precision comparisons, and testing on the
affected GenomeDK host with the user's datasets. A successful run here does not
establish that the reported crash is repaired. Historical MKL settings remain
experimental even if they complete: a non-crashing baseline cannot demonstrate
that a setting cures the failure, or that old MKL honored it.
