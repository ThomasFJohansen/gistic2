# GISTIC2
This repository contains the Matlab source code for GISTIC (**G**enomic **I**dentification of **S**ignificant **T**argets **I**n **C**ancer), version 2.0.

Check out the <a href="https://broadinstitute.github.io/gistic2">GISTIC GitHub Page</a> for links to GISTIC downloads, user documentaion, and publications.

**Note from forker:** Forked this to attempt to fix the issues experienced on modern AMD CPU's. 

## Cloning the gistic2 project
This repository contains a submodule of matlab functions for processing copy number data named 'snputil.'
To ensure that the snputil subdirectory is populated with files, you should clone this repository using
the *--recursive* option:
```
git clone --recursive  https://github.com/ThomasFJohansen/gistic2.git
```
## Repository directory structure
> *docs* - HTML source for links and user documentation published in the GISTIC GitHub page.

> *refgenes* - source code for creating reference genome input files (offered on an 'as is' basis).

>> *Gencode.v22.170324* - download EMBL files and build a Gencode reference genome.

>> *hg38.UCSC.add_mir.160920* - download UCSC files and build an hg38 reference genome.

> *snputil* - git submodule of utility Matlab functions for analyzing copy number data.

>> *@SegArray* - defines the SegArray class, a data compression scheme for segmented copy number.

> *source* - Matlab source code for GISTIC.

> *support* - additional files needed to build a GISTIC tarball.

> *user_docs* - HTML source for standalone documentation in the current GISTIC tarball (v2.0.23).


## Modern Linux/HPC work in this fork

The `modernize-runtime-hpc` branch adds an explicit compatibility launcher,
reproducible build tooling and scientific regression checks. **The reported AMD
floating-point crash is not yet established as fixed. No modern standalone
executable has been rebuilt.** The MATLAB scientific source, submodule revision,
legacy binary, model and thresholds are unchanged.

The launcher supports the original 2.0.23 **R2014a/Runtime 8.3 executable** and
future builds with ABI metadata. The binary historically checked into `support/`
actually requests MCR 7.14; it is not the R2014a release executable. Supply an
original release binary using `scripts/prepare_legacy.sh` instead of trying to
repair this mismatch by renaming Runtime libraries.

```bash
# Use absolute paths; preserve the original installation.
./scripts/prepare_legacy.sh /original/gp_gistic2_from_seg /runtime/v83 /new/candidate
GISTIC_COMPAT=off /new/candidate/run_gistic_example /new/example-off
GISTIC_COMPAT=single /new/candidate/run_gistic_example /new/example-single
```

`off` is the default. `threads` limits OMP/MKL/OpenBLAS threads; `affinity` chooses
one allowed logical CPU; `single` combines both. Affinity respects the current
cpuset/Slurm allocation and requires `taskset` from util-linux. No CPU-vendor
autodetection or implicit historical MKL override is used. Bash, coreutils and
Linux `/proc` are required. Arguments are quoted and forwarded without changing
the GISTIC CLI, including calls from R/blit. Library overrides are isolated and
DISPLAY unset by default; documented opt-ins permit deliberate overrides.

- [Investigation, source audit and hypotheses](docs/modernization/INVESTIGATION.md)
- [Measured results, compatibility matrix and remaining gates](docs/modernization/RESULTS.md)
- [Licensed modern MATLAB build and source execution](docs/modernization/BUILD.md)
- [Regression commands and comparison policy](docs/modernization/TESTING.md)
- [GenomeDK, TCGA-BRCA, blit and Apptainer instructions](docs/modernization/GENOMEDK.md)

The original installation documents remain in `support/` and `user_docs/` for
historical reference. The new workflow does not redistribute MATLAB Runtime or
claim support for untested MATLAB releases, physical CPUs, containers or cohorts.
