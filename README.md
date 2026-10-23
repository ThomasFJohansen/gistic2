# GISTIC2
This repository contains the Matlab source code for GISTIC (**G**enomic **I**dentification of **S**ignificant **T**argets **I**n **C**ancer), version 2.0.

Check out the <a href="https://broadinstitute.github.io/gistic2">GISTIC GitHub Page</a> for links to GISTIC downloads, user documentaion, and publications.

**Note from forker:** Forked this to attempt to fix the issues experienced on modern AMD CPU's. 

## MATLAB R2026b build

The `matlab-r2026b` branch updates the source for **MATLAB Runtime R2026b (26.2)**.
Compile on Linux x86-64 with MATLAB R2026b, MATLAB Compiler, Statistics and
Machine Learning Toolbox, and a supported C compiler:

```matlab
mex -setup C
build_gistic
```

See [build and run instructions](BUILD_R2026b.md). Compilation and testing on the
original failing data are pending. This branch applies no single-CPU workaround.
MathWorks currently advises RHEL/SUSE-based distributions to wait for
**R2026b Update 1** because of an issue in the initial Runtime release.

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

