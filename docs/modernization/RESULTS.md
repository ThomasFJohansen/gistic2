# Validation results and compatibility matrix

This report distinguishes measured results from pending release gates. The
reported AMD floating-point exception **was not reproduced** in this environment,
so it cannot be declared fixed. Unrestricted execution succeeds locally; that
does not show that restrictions can be removed on an affected machine.

## Environment and artifacts actually tested

All measurements below use the original **GISTIC 2.0.23 executable** from pinned
GenePattern commit `9455555051a59a2aa095bc84834227622b13bec1`, original MATLAB
Runtime **8.3.0.532 / R2014a**, MKL library **11.0.5 build 20130612**, and the official
standalone example. The guest exposes **AMD EPYC 9V74**, AuthenticAMD,
family 25/model 17, x86-64, **9 CPUs, KVM**. The physical CPU is unverified. Linux is
Ubuntu **24.04.3**, kernel **6.18.55**, glibc **2.39-0ubuntu8.6**. Real Ubuntu
ncurses/tinfo ABI-5 compatibility libraries are added privately. Every run has
fresh output/cache directories and identical inputs/options. SHA-256 hashes and
complete guest flags are in [environment.json](validation/2026-10-22/matrix/environment.json).

## Seven-condition original-runtime matrix

| Configuration | Exit | Wall seconds | Child CPU seconds | Scientific comparison |
| --- | ---: | ---: | ---: | --- |
| Original launcher, unrestricted | 0 | 150.02 | 161.30 | Reference, complete |
| New launcher, `off` | 0 | 158.02 | 167.83 | Exact match |
| `threads` only | 0 | 154.03 | 164.75 | Exact match |
| `affinity` only | 0 | 154.03 | 150.46 | Exact match |
| `single` (both) | 0 | 150.02 | 146.66 | Exact match |
| `MATLAB_DISABLE_CBWR=1`, `MKL_CBWR=SSE4_2` | 0 | 153.02 | 162.74 | Exact match |
| `MKL_DEBUG_CPU_TYPE=4` | 0 | 152.03 | 159.01 | Exact match |

“Exact match” means all **14 scientific text tables** match at zero tolerance
and the four required full-precision MAT outputs match recursively:
`scores.0.5.mat`, `peak_regs.mat`, `wide_peak_regs.mat`, `perm_ads.mat`.
This includes amplification/deletion peaks, G-scores, q-values represented in
these outputs, coordinates, gene/sample identities and null-model output.
All three gene-data tables contain 17,458 genes plus a header. The MAT readers
used NumPy 2.3.5, SciPy 1.17.0 and h5py 3.16.0. A licensed MATLAB comparison was
not possible. `orig_stats.mat` and `gene_stats.mat` were not emitted by this
example configuration and are explicitly unverified.

[review.json](validation/2026-10-22/matrix/review.json) contains the scientific
review, comparator hashes and confirmation that every saved output hash still
matches its original run. Original stdout/stderr and per-run measurements are
retained beside it. The raw harness initially marked these runs failed because
its expected BED filename omitted `.conf_90`. The comparator also needed to allow
identical empty padding cells in the gene-summary tables. Both validator mistakes
were fixed and regression-tested. **Raw logs/results are retained unmodified**;
the separate review rechecks the already saved outputs with the corrected
validator. These were validation-tool defects, not crashes or altered GISTIC
results.

These single-pass timings span 150–158 seconds. The new unrestricted launcher
was 5.3% slower in this pass, while combined restriction was essentially the same
wall time as the original. This does not establish a real speed difference:
Runtime startup, OS page cache, guest scheduling, interactive host work and
nonrandom case ordering are confounders. There is no demonstrated speedup or
performance guarantee for large cohorts. The CPU time reduction under affinity
is consistent with less parallel execution, not proof of a numerical-library
repair. Historical MKL modes remain experimental because dispatch selection is
unverified and the baseline already succeeds.

## Reproducibility and external reference checks

A second original/off/single series completed and matched the first original
run in all text tables and all four required MAT outputs. The execution transcript
recorded these measurements:

| Second execution | Wall seconds | Child CPU seconds | Scientific comparison |
| --- | ---: | ---: | --- |
| Original | 154.03 | 164.20 | Exact match |
| New launcher `off` | 157.05 | 168.73 | Exact match |
| `single` | 157.04 | 153.40 | Exact match |

A later environment reset removed those repeat-run raw files before they were
committed. These are observed results, but the repository cannot independently
recheck their raw artifacts. The first seven-case matrix above has retained logs,
measurements, hashes and scientific review. Do not combine the repeat timings
into a stronger performance claim.

Repeated process inspection observed CPUs `0-8` and 33 OS threads for `off`,
and CPU `0` (the first permitted CPU, not hardcoded) with 17 OS threads for
`single`. Both mapped this Runtime's MKL, mklcompat, BLAS, LAPACK, libmwmathelem,
and libiomp5 libraries. These observations likewise precede the reset. A single
permitted CPU does not imply a single OS thread; Java/Runtime support threads
persist. The selected MKL instruction branch remains unverified.

The unrestricted GenePattern profile also completed (169.06 wall seconds,
174.73 child CPU seconds) and exactly matched all 12 published text tables;
that result was observed in the transcript but its raw files were lost. The
unfinished restricted GenePattern check is being rerun against the independently
published tables; it is not counted as passed until its results are retained.

The independent GenePattern tables were fetched from a pinned commit and all
12 Git blob hashes/sizes verified. Their profile differs from the standalone
example (join size 4, broad analysis off, arm peeling off). The four text inputs
match GenePattern's input Git blobs exactly. The separately hosted
`Human_Hg16.mat` download returns HTTP 503, so identity with the local hg16
reference is not established from input bytes alone.

## Successful, failed and unavailable tests

| Test | Result and scope |
| --- | --- |
| 27 Python unit tests | Passed; launcher/validator behavior and optional full-precision reader tests |
| Bash syntax / Python compilation / Git whitespace checks | Passed |
| Stale repository binary with Runtime 8.3 | Reproduced loader error requesting MCR 7.14; unrelated to peak-stage crash |
| Original R2014a installation and example | Completed; no native crash |
| New launcher/mode matrix | Complete, exact within-environment outputs as above |
| Truncated gene table detection | Tested and rejected; finite scores, matching row/sample identities required |
| Modern build invocation | Correctly stops: MATLAB/Compiler unavailable; no binary produced |
| Licensed source execution/MEX rebuild/MATLAB comparison | Blocked: tools/licenses unavailable |
| Physical affected AMD, Intel comparison, RHEL 9 | Unverified: target hardware/OS not available |
| Apptainer/Singularity/Docker/Podman execution | Unverified: no container engine installed |
| Patient cohorts / failing dataset / minimized native reproducer | Unverified: data and crash dump unavailable |
| Loaded native libraries / MKL dispatch branch | Runtime library paths observed in repeated off/single maps; selected instruction branch remains unverified |

The October 21 session had an incomplete focal gene table despite a successful
process exit. That baseline was rejected. Its scratch files were lost at the
session reset, and the suggested synchronization explanation was not proven.
The October 22 reruns use `/tmp` during execution and archive only completed
outputs; all retained gene tables pass consistency checks. No October 21 timing
or output is used as a trusted result in this report.

## Compatibility claims

| Application/runtime | Platform | Status |
| --- | --- | --- |
| Official 2.0.23 / R2014a 8.3 | AMD-exposed KVM, Ubuntu 24.04/glibc 2.39, private ABI-5 libs | Example succeeds unrestricted and all tested restrictions; exact outputs |
| Repository stale binary / R2014a 8.3 | Same guest | Incompatible loader ABI (requests 7.14) |
| Official 2.0.23 / R2014a | Affected physical AMD / RHEL 9 | Reported user failure; not validated by our guest results |
| Modern source / R2026a or another selected supported release | Licensed Linux build host | Build procedure prepared, not compiled or validated |
| Modern rebuilt executable / matched modern Runtime | AMD or Intel Linux/HPC | No artifact built; unverified |
| Any tested executable / container | Host-dependent | Recipe only; unverified |

## Changed files

- `support/gistic2`: relocatable, quoted launcher; Runtime ABI checks, headless and
  library isolation controls, explicit thread/affinity modes and status propagation.
- `support/run_gistic_example`: absolute input paths, quoted arguments and refusal
  to overwrite existing output directories.
- `scripts/build.sh`, `build_gistic.m`: staged licensed build, source provenance,
  fresh MEXes, valid-input SegArray checks and Runtime ABI metadata.
- `scripts/prepare_legacy.sh`, `diagnose.sh`: preserve the original installation,
  stage the launcher and collect selected diagnostic information.
- `scripts/regression.py`, `compare_outputs.py`, `compare_mat_outputs.py`,
  `review_results.py`, `fetch_reference.py`: serial experiments, strict scientific
  checks, retained-output review and pinned published reference retrieval.
- `tests/`: portable tests, pinned GenePattern manifest, MATLAB SegArray and
  full-precision comparison functions.
- `.github/workflows/portable-tests.yml`: portable CI; it does not claim MATLAB validation.
- `.gitignore`, `README.md`, `docs/modernization/`: artifact exclusions, installation,
  build/testing guidance, investigation and actual validation evidence.

Scientific MATLAB source, snputil gitlink, original binary, reference inputs,
licenses and legacy installation/release documents are unchanged. No proprietary
Runtime or new compiled artifact is committed. Work stays on a feature branch;
the default branch is not modified.
