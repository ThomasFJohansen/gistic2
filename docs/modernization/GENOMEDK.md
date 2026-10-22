# GenomeDK deployment and validation

These are commands to run on your account; they have not been executed on
GenomeDK. Your reported environment is AMD x86-64, kernel 5.14, RHEL 9-family,
GISTIC 2.0.23 with Runtime 8.3. Our Ubuntu/KVM test environment differs.

## Keep the original installation and stage the new launcher

Set these paths to your existing files. `GISTIC_TEST_ROOT` must be a new directory
on your project filesystem; it is not a replacement for the original installation.

```bash
export GISTIC_REPO=/absolute/path/to/gistic2
export GISTIC_ORIGINAL=/absolute/path/to/original/GISTIC
export GISTIC_RUNTIME=/absolute/path/to/MATLAB_Compiler_Runtime/v83
export GISTIC_TEST_ROOT=/absolute/path/to/project/gistic-validation-20261022

git clone --recursive --branch modernize-runtime-hpc \
  https://github.com/ThomasFJohansen/gistic2.git "$GISTIC_REPO"
mkdir "$GISTIC_TEST_ROOT"
"$GISTIC_REPO/scripts/prepare_legacy.sh" \
  "$GISTIC_ORIGINAL/gp_gistic2_from_seg" "$GISTIC_RUNTIME" \
  "$GISTIC_TEST_ROOT/legacy-candidate"
```

Use the official R2014a executable from your working distribution. The executable
committed in `support/` is a different, older build that requests MCR 7.14.
`prepare_legacy.sh` rejects that known stale hash. It never replaces your binary
or Runtime. If the original binary is inside a SIF, use the container approach
below rather than mixing its libraries with the host.

## Submit the controlled example matrix to AMD nodes

Run computations through the queue, with your project account. GenomeDK documents
an `amd` node feature, but confirm the current features with `scontrol show node`.
Do not assume CPUs are numbered from zero within your allocation.

Save this as `$GISTIC_TEST_ROOT/example-matrix.sbatch`:

```bash
#!/usr/bin/env bash
#SBATCH --job-name=gistic-regression
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=02:00:00
set -euo pipefail
: "${GISTIC_REPO:?}" "${GISTIC_ORIGINAL:?}" "${GISTIC_RUNTIME:?}" "${GISTIC_TEST_ROOT:?}"
export GISTIC_EXECUTABLE="$GISTIC_ORIGINAL/gp_gistic2_from_seg"
"$GISTIC_REPO/scripts/diagnose.sh" > "$GISTIC_TEST_ROOT/environment-$SLURM_JOB_ID.txt"
python3 "$GISTIC_REPO/scripts/regression.py" \
  --runtime "$GISTIC_RUNTIME" --executable "$GISTIC_EXECUTABLE" \
  --original-launcher "$GISTIC_ORIGINAL/gistic2" \
  --output "$GISTIC_TEST_ROOT/matrix-$SLURM_JOB_ID" \
  --cases original off threads affinity single --experimental-mkl --repeats 3
```

Submit with the variables exported above:

```bash
sbatch --account=YOUR_PROJECT --constraint=amd --export=ALL \
  "$GISTIC_TEST_ROOT/example-matrix.sbatch"
```

This reserves one consistent allocation for all cases. The original launcher must
already point to the correct Runtime and use the same executable. If it is broken
for path reasons, repair a copy and record that change separately; do not call that
an untouched original-launcher comparison. The matrix clears inherited dispatch
and thread settings. `threads` sets three thread variables; `affinity` chooses one
permitted CPU; `single` does both. Neither guarantees the MATLAB process contains
only one OS thread. The default `off` imposes neither restriction.

If you use node-local storage, run the full matrix there and copy it to the project
only after completion, including failed-run logs. Allow sufficient disk for every
output and fresh Runtime cache. Retain CPU model, allowed set, OS, Runtime version,
input hashes, exit code, crash report and complete stdout/stderr. The harness
records inaccessible process maps as unavailable rather than guessing the loaded
MKL dispatch branch.

## Run your TCGA-BRCA inputs with unchanged scientific arguments

First copy the **exact arguments emitted by blit** into a JSON array, omitting
`-b` and its destination. Keep the same hg19/hg38 reference, segmentation file,
sample selection, confidence, and thresholds. Do not substitute the hg16 example
reference for patient data. For example, the minimal structure is:

```json
["-seg", "/absolute/TCGA-BRCA.seg", "-refgene", "/absolute/matching-reference.mat"]
```

Append every option from your real invocation. A custom matrix can then use:

```bash
python3 "$GISTIC_REPO/scripts/regression.py" \
  --runtime "$GISTIC_RUNTIME" \
  --executable "$GISTIC_ORIGINAL/gp_gistic2_from_seg" \
  --args-json "$GISTIC_TEST_ROOT/brca-arguments.json" \
  --output "$GISTIC_TEST_ROOT/brca-matrix-$SLURM_JOB_ID" \
  --cases off threads affinity single --repeats 2
```

Execute this inside a Slurm job with resources appropriate to the real cohort.
The provided validator targets confidence 0.90 and unprefixed example-style
outputs. If blit uses another confidence, a filename prefix, or disables outputs,
adapt the validation schema to those expected files; a schema failure is not a
MATLAB crash. Preserve all raw results. Compare against an independently trusted
successful run of the same cohort where available. Analyze each PAM50 cohort
separately; an example pass cannot establish BRCA correctness.

To use the launcher from the existing R workflow, point blit's existing executable
configuration at `$GISTIC_TEST_ROOT/legacy-candidate/gistic2`. Its `-seg`, `-refgene`,
`-b` and other application arguments pass through unchanged. Before running the
same existing R calls, choose the mode in the parent environment:

```bash
export GISTIC_COMPAT=single
# Invoke your existing R/blit script with the candidate launcher path.
Rscript /absolute/path/to/your-existing-analysis.R
```

Or set `Sys.setenv(GISTIC_COMPAT = "single")` before the existing `blit::gistic2()`
/ `blit::cmd_run()` invocation. Set `GISTIC_COMPAT=off` for the unrestricted
comparison. No R-package source change is required by this launcher design.
Actual blit integration remains unverified here because R, blit and your analysis
script/data are unavailable. Do not infer a blit argument name from this example;
keep the executable-path mechanism already used by your installation.

## Apptainer/Singularity

GenomeDK supports Apptainer. Pull/convert images once before submitting jobs,
then record `sha256sum image.sif`; do not use a changing `latest` tag as provenance.
A container shares the host CPU and kernel, so an older userspace alone does not
remove a CPU-dispatch problem. No container engine is available in our test host;
this workflow is unverified.

For your existing `gistic_latest.sif`, first inspect actual paths:

```bash
apptainer exec --cleanenv gistic_latest.sif /bin/bash -c \
  'command -v taskset; ls -l /opt/GISTIC; find /opt -name libmwmclmcrrt.so.8.3 -print'
```

After confirming those paths, bind the repo and project to the **same absolute
paths** in the container and invoke the new launcher against the original binary.
Inside a Slurm allocation, for an image with the paths below:

```bash
apptainer exec --cleanenv \
  --bind "$GISTIC_REPO:$GISTIC_REPO:ro" \
  --bind "$GISTIC_TEST_ROOT:$GISTIC_TEST_ROOT" \
  --env GISTIC_EXECUTABLE=/opt/GISTIC/gp_gistic2_from_seg \
  --env GISTIC_MCR_ROOT=/opt/GISTIC/MATLAB_Compiler_Runtime/v83 \
  --env GISTIC_COMPAT=single \
  gistic_latest.sif \
  "$GISTIC_REPO/support/run_gistic_example" \
  "$GISTIC_TEST_ROOT/container-single-$SLURM_JOB_ID"
```

Change only confirmed image paths. Bind real input/reference directories read-only
for your BRCA invocation and bind a writable output/cache location. `--cleanenv`
requires passing `GISTIC_*` choices explicitly with `--env`; host exports alone
may be removed. Older Singularity installations can use their equivalent options.
If `taskset` is missing inside the image, `single` fails clearly; install util-linux
when building the image or select `threads` explicitly (which is a different test).

For a modern candidate, first build using [BUILD.md](BUILD.md), then use a
MathWorks Runtime image matching that exact release/update. The
[official Runtime containers](https://www.mathworks.com/help/compiler_sdk/ml_code/get-matlab-runtime-container.html)
are deployment environments, not Compiler licenses. Pin the image digest and
configure Java if required. Test unrestricted and restricted runs on the same
node; do not claim modern compatibility from an image pull alone.

## Troubleshooting

| Symptom | Action |
| --- | --- |
| Requests MCR 7.14 while launcher says v83 | Wrong executable; obtain the official 2.0.23 R2014a binary. Changing a directory name does not change its ABI. |
| Missing `libmwmclmcrrt.so.*` | Match executable/compiler release, ABI metadata and the direct Runtime root. |
| Missing `libncurses.so.5`/`libtinfo.so.5` | Use real ABI-5 compatibility packages for the target OS, or a compatible container. Do not symlink ABI-6 libraries to ABI-5 names. Ubuntu packages used in our test are not an RHEL installation recipe. |
| `refblas.so` load failure | Inspect `BLAS_VERSION`, `LAPACK_VERSION`, `LD_PRELOAD`, library paths and MATLAB release. Default launcher isolation clears inherited overrides. Do not force an arbitrary system BLAS. |
| Floating-point exception / SIGSEGV | Retain crash dumps/logs; run the isolated matrix. A stack frame in `libmwmathelem.so` is not proof of an MKL-dispatch defect. |
| `crosses chromosomes` | Check source/build provenance; upstream's `chr_max` source fix is already in this fork but may be absent from a historical compiled binary. |
| Exit 0 but missing/truncated tables | Treat as failure; GISTIC catches some MATLAB errors. Check logs, filesystem space, and table identities. |
| `taskset` unavailable or CPU outside allocation | Install util-linux or choose `threads`; never force CPU 0 or broaden a scheduler allocation. |

The launcher isolates inherited library/BLAS/MATLAB overrides by default and
unsets DISPLAY for headless execution. `GISTIC_INHERIT_LIBRARY_ENV=1` and
`GISTIC_HEADLESS=0` are explicit escape hatches for a deliberately configured
installation. `GISTIC_EXTRA_LIBRARY_PATH` adds known absolute compatibility-library
directories without inheriting unrelated Conda/system libraries. Historical MKL
settings are not automatic defaults: use only as separately recorded experiments.
