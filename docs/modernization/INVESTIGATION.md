# GISTIC2 AMD/Linux investigation

Date: 2026-10-22. Scope: ThomasFJohansen/gistic2, upstream Broad GISTIC 2.0.23,
recursive snputil dependency. **Root cause remains unconfirmed.** The official
example did not reproduce the reported floating-point exception on our
AMD-exposed KVM guest. Passing comparisons are compatibility evidence for the
measured configuration, not proof that the GenomeDK failure is resolved.

## Evidence and provenance

The user's reported failure is during peak detection on a modern AMD GenomeDK
node, kernel 5.14/RHEL 9-family, Runtime 8.3.0.532 (R2014a), with a frame in
`libmwmathelem.so`, floating-point exception followed by segmentation fault and
status 139. Different PAM50 cohorts reach different chromosomes. These reports
are input to the investigation; the patient datasets and crash dump are not
available in this environment.

The required initial inspection was repeated after the session environment reset:
`lscpu`, full `/proc/cpuinfo`, `uname -a`, `ldd --version`. The guest exposes
AuthenticAMD, EPYC 9V74 80-Core Processor, family 25/model 17/stepping 1, x86-64,
9 logical CPUs (0-8), KVM full virtualization. Available ISA includes SSE through
SSE4.2/SSE4a, AVX/AVX2/FMA, BMI1/2, AES/SHA, AVX512F/DQ/CD/BW/VL/IFMA/BF16,
VBMI/VBMI2/VNNI/BITALG/VPOPCNTDQ. The full flags, affinity and cgroup quota are
retained in validation metadata. OS is Ubuntu 24.04.3 LTS, kernel 6.18.55,
glibc 2.39-0ubuntu8.6. **Neither CPUID nor `/proc/cpuinfo` verifies the underlying
physical CPU.** This is not bare-metal AMD or GenomeDK/RHEL validation.

Pinned original-runtime experiment assets (downloaded outside Git):

| Asset | Provenance | SHA-256 |
| --- | --- | --- |
| R2014a Linux x86-64 installer | [MathWorks installer](https://ssd.mathworks.com/supportfiles/downloads/R2014a/deployment_files/R2014a/installers/glnxa64/MCR_R2014a_glnxa64_installer.zip) | `fba9cf6dc896bf613d92b4c1cbdb50708b1bef8514bf52a5ad14527c38824a15` |
| GISTIC 2.0.23 executable requiring 8.3 | [GenePattern pinned executable](https://github.com/genepattern/GISTIC_2.0/blob/9455555051a59a2aa095bc84834227622b13bec1/gp_gistic2_from_seg) | `1045c8372d58b26a8638b703d054e80472bb1527fcf015921344b5f299921576` |
| Repository's stale executable requiring 7.14 | `support/gp_gistic2_from_seg` | `576196ec20117e0543cb3948ed4149348b496ce6cccc83094a331487ddb4f821` |
| libncurses5 Ubuntu package 6.3-2ubuntu0.3 amd64 | [Ubuntu archive](https://archive.ubuntu.com/ubuntu/pool/universe/n/ncurses/libncurses5_6.3-2ubuntu0.3_amd64.deb) | `58da01991712c6856af0658dc5e9cb533c1a6854ab950055ade185e35bc9c276` |
| libtinfo5 Ubuntu package 6.3-2ubuntu0.3 amd64 | [Ubuntu archive](https://archive.ubuntu.com/ubuntu/pool/universe/n/ncurses/libtinfo5_6.3-2ubuntu0.3_amd64.deb) | `4df4288404108f1a156d014e8764a064e977e34e6d44931ab60451694c03c90d` |

The Runtime installer completed successfully. Ubuntu 24.04 lacks the needed
ncurses ABI 5; genuine Ubuntu compatibility packages were extracted into a
private directory and supplied through `GISTIC_EXTRA_LIBRARY_PATH` for every
case. No global libraries were replaced. This changes userspace dependencies
relative to GenomeDK and limits extrapolation. The original Broad FTP archive
was unavailable during the earlier session (timeout/HTTPS 503), so the executable
came from the first-party GenePattern repository rather than an unverified
third-party container. The example inputs and hg16 reference came from this
source checkout; their SHA-256 hashes accompany each run.

Directly loading the installed `mkl.so` and calling `MKL_Get_Version_String`
reported Intel MKL **11.0.5, build 20130612**, Intel 64 architecture. This identifies
the installed library, not the dispatch branch actually chosen by MATLAB.
Process maps are restricted/inaccessible in this sandbox; failed attempts are
recorded. No claim is made that `MKL_CBWR`/`MKL_DEBUG_CPU_TYPE` was honored.

## Upstream reports and what they establish

- [Issue 27](https://github.com/broadinstitute/gistic2/issues/27) and
  [issue 12](https://github.com/broadinstitute/gistic2/issues/12) describe a binary
  requesting MCR 7.14 despite v83 installation instructions. We reproduced that
  loader mismatch with the checked-in binary. It is distinct from the 8.3 peak
  detection crash. A new Runtime alone cannot make an old binary compatible.
- [Issue 9](https://github.com/broadinstitute/gistic2/issues/9) has heterogeneous
  crash reports. Unsetting DISPLAY helps one reporter but not another; a separate
  report says fewer CPUs help. The modern AMD report combines affinity and
  thread restrictions and explicitly leaves causation unknown. Our matrix
  separates those variables and uses headless operation for all cases.
- [Issue 22](https://github.com/broadinstitute/gistic2/issues/22) is a missing
  `refblas.so` error at `SegArray/nnz` with newer MATLAB. It supports auditing
  library resolution; it does not identify a particular environment variable
  or prove the AMD crash is a BLAS loader problem.
- [Issue 6](https://github.com/broadinstitute/gistic2/issues/6) is a separate
  chromosome-boundary source defect. The maintainer's `chr_max` correction is
  already present (commit `6b880d34c7295db142e63a0b40cb29f9aee2b465`). It is not
  reapplied. Historical compiled executables may predate that source change.
- [Eigenvector's first-party product report](https://www.eigenvectordocs.com/index.php?title=Faq_how_to_fix_AMD_cpu_bug_in_Intel_Math_Kernel_Library)
  describes rare AMD crashes in its R2014a-built Solo products and reports no
  such known crashes in newer R2020b-built products. It suggests the two
  historical MKL settings tested here. This is related evidence from another
  application, not a demonstrated GISTIC fix.
- [MathWorks bug 1043644](https://www.mathworks.com/support/bugreports/1043644)
  required sign-in and its technical contents were unavailable. No undocumented
  details or exact affected processor list are inferred from it.
- MathWorks' [Runtime deployment documentation](https://www.mathworks.com/help/compiler_sdk/ml_code/install-the-matlab-runtime.html)
  and [compatibility rule](https://www.mathworks.com/help/compiler_sdk/ml_code/about-the-matlab-runtime.html)
  require a release-matched Runtime, at the compiler's update level or newer.
  These support rebuilding, not substituting a newer Runtime under the old binary.

## Recursive source/build audit

The fork's starting commit was `08ec37ad6620e6c7ab707be8f8173723d9ed4500`.
Upstream was `26c590bd3330aafa27618ef3eb4b8d9b301f06b7`; the fork's two later
commits only changed README text/clone URL. The recursive snputil revision is
`cf3172b858c6ceea1688816e632228c89ba80e89` and remains unchanged.

`source/gp_gistic2_from_seg.m` parses the standalone/GenePattern options and calls
`run_gistic2_from_seg`, then the scoring/permutation/focal pipeline. Some caught
`snp:` errors are printed without a nonzero process exit, which is why exit 0 is
insufficient. Peak logic includes `identify_peaks_by_arbitration`, wide-peak
interval calculations and chromosome bounds. The last logged chromosome does
not identify the native crashing primitive.

Numerical operations include `nanmean`/`nanmedian`, histograms (`histc`), sorting,
interpolation, convolutions of null distributions and `normcdf`. `lunique.m`
explicitly preserves historical uniqueness semantics. These operations and
scientific thresholds were not rewritten. BLAS is involved in operations such
as the vector inner product in `snputil/@SegArray/nnz.m`; MATLAB's implementation
of other numerical primitives is closed source. A MATLAB native stack alone
cannot distinguish those implementations from MKL dispatch.

`SegArray` is a classdef class with many MATLAB methods and two public static
C MEX helpers, `cosort.c` and `sumranges.c`. Old `.mexa64` artifacts dynamically
link MATLAB's mx/mex/mat libraries. They use the separate-complex `mxGetPr` API.
The new build stages and recompiles both helpers rather than carrying those
binaries forward. Their existing C code has limited defensive validation and
integer-size assumptions; they are not proven to cause the reported failure and
are not changed without a reproducer and separate scientific regression.
`match_string_sets_hash` uses Java, so removing the JVM is not an acceptable
headless workaround.

Historical source notes require MATLAB R2010b or newer and mention compatibility
through R2016a, with graphics differences starting R2015a. These are historical
claims, not current support evidence. The release shell script hardcodes Broad
SVN/site paths and a MATLAB 2014a compiler. The old launcher depends on cwd,
unquoted `$@`, inherited library paths and an incorrect X resource path. The
new launcher locates itself, quotes arguments, checks Runtime structure, offers
explicit library isolation and uses `exec` to propagate status/signals. Standard
application options and output formats remain unchanged.

The repository provides official example segmentation/marker/sample/CNV files
and several reference MAT files, but no usable automated end-to-end regression
suite. GenePattern publishes additional expected tables with different options;
we pin and validate them separately. All new scripts/tests are outside the
scientific source/submodule; see RESULTS for the changed-file inventory.

## Competing hypotheses

| Hypothesis | Supporting evidence | Evidence limiting the conclusion | Test and current status |
| --- | --- | --- | --- |
| A. Old MKL CPU dispatch | R2014a/AMD reports in another compiled application; old MKL 11.0.5 installed | No local crash; libmwmathelem frame is not a dispatch trace | Separate SSE4_2/disable-CBWR and debug CPU type experiments executed; dispatch selection itself unverified |
| B. Old MATLAB numerical library | Reported native frame is in libmwmathelem | Frame may be downstream of bad input/state; proprietary code cannot be audited | Original Runtime example executed; modern licensed MATLAB/rebuild blocked |
| C. Threading/concurrency | Reduced CPU count and combined restriction reportedly help | Report changes two variables; Runtime creates non-numerical threads too | Thread-only, affinity-only and combined matrix executed; successful baseline prevents identifying a necessary restriction |
| D. ISA/microarchitecture/FP behavior | Failure reported on modern AMD, ancient native libraries | Guest feature exposure is not physical attestation; local baseline succeeds | Guest ISA recorded; physical AMD/Intel cross-host runs and crash-instruction analysis unavailable |
| E. glibc/library resolution | Very old Runtime on modern Linux; missing ncurses ABI observed; separate BLAS issue | Loader failure differs from peak-stage FPE; Ubuntu run succeeds with real ABI-5 libs | Dependency resolution and isolated launcher tested; RHEL/container comparison blocked |
| F. Input degeneracy | Cohorts fail at different chromosomes; numerical/index edge cases plausible | Official example reportedly also fails on affected host; no failing inputs available here | Official example checked for complete finite score outputs; patient cohorts, minimal reproducer and denominator/index instrumentation unavailable |
| G. Independent source bug | Upstream chromosome-boundary defect confirmed and fixed | Already merged; not evidence for this native AMD failure | Source audit performed; no unrelated statistical patch added; rebuilt application still required to incorporate post-release fixes |
| H. Interaction | Hardware, old Runtime, OS and inputs may interact | No factorial experiment with a reproducing failure yet | Matrix isolates practical restrictions on one guest; retain same-host failing baseline for next investigation |

To resolve causation, reproduce on an affected node, retain the native crash dump,
identify the signal and instruction address, map the loaded libraries and versions,
and change one condition at a time. Compare the same dataset under source MATLAB
and a matched modern compiled build. A container can isolate userspace while
retaining the CPU/kernel. Do not suppress numerical exceptions, remove samples,
replace nonfinite values, or adjust statistical thresholds to obtain completion.
