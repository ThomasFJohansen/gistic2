# Building with a modern MATLAB release

**Status: build workflow implemented, but not executed here.** This environment
has no MATLAB, MATLAB Compiler, or licenses. No rebuilt standalone executable
is included. The checked-in historical binary is unchanged.

## Choose a release and build host

As checked on 2026-10-22, R2026b is current. MathWorks' Runtime download page warns
that its initial Runtime has a problem on RHEL/SLE distributions and recommends
waiting for Update 1. R2026a with its latest update is therefore a practical
candidate for the first GenomeDK rebuild, not a tested GISTIC compatibility
claim. Recheck the [Runtime release notice](https://www.mathworks.com/products/compiler/matlab-runtime.html)
before choosing a version. R2024b/R2025a are alternative candidates if your
licensed site supports them; they have not been tested in this fork either.

Use a Linux x86-64 build host supported by that MATLAB release and a supported C
compiler. Install MATLAB, MATLAB Compiler, and Statistics and Machine Learning
Toolbox. A Runtime installation alone cannot compile or execute arbitrary `.m`
source. `normcdf` and legacy `nan*` functions make the Statistics dependency
relevant. Check the selected release's supported OS/compiler requirements.

```bash
git clone --recursive --branch modernize-runtime-hpc https://github.com/ThomasFJohansen/gistic2.git
cd gistic2
git submodule update --init --recursive
export MATLAB_BIN=/absolute/path/to/MATLAB/R2026a/bin/matlab
"$MATLAB_BIN" -batch "mex -setup C"
./scripts/build.sh "$PWD/build/R2026a-candidate"
```

`build.sh` refuses to replace an existing destination. It records the source
commit, submodule commit, local diff, MATLAB/toolbox versions and BLAS/LAPACK
version strings. `build_gistic.m` stages the source, deletes staged old MEX
binaries, rebuilds **both** `SegArray.cosort` and `SegArray.sumranges`, runs valid
SegArray operation tests, and invokes `mcc` on `gp_gistic2_from_seg.m`. It includes
the utility tree for deployed dependencies and writes `runtime-abi.txt` and
`matlab-version.txt` beside the executable. The source checkout is not altered.

The MEX build explicitly uses the separate-complex API (`-R2017b`) and
`-largeArrayDims`, consistent with the existing `mxGetPr` code. Recompilation
addresses binary ABI compatibility; it does not prove correctness or fix
existing C input-validation limitations. Do not reuse the checked-in `.mexa64`
files with a new MATLAB release. See [MathWorks MEX compatibility](https://www.mathworks.com/help/matlab/matlab_external/do-i-need-to-upgrade-my-mex-files-to-use-interleaved-complex.html).

Do not compile with `-nojvm`: `match_string_sets_hash.m` uses Java Hashtable.
For releases that require a separately installed Java runtime, follow the
[release-specific JRE instructions](https://www.mathworks.com/help/compiler/configure-matlab-runtime-to-use-java.html)
and configure it with `matlab_jenv`. Headless operation uses `-nodisplay`.

## Source execution and modern compiled execution

After the build stages and rebuilds the MEXes, licensed MATLAB can execute the
staged source without Compiler Runtime. Use absolute paths and the exact same
arguments as your baseline. For example, in MATLAB:

```matlab
addpath('/absolute/build/R2026a-candidate/build-source/source');
addpath('/absolute/build/R2026a-candidate/build-source/snputil');
% Create a NEW output directory before this call.
gp_gistic2_from_seg('-b','/absolute/new-output', ...
    '-seg','/absolute/examplefiles/segmentationfile.txt', ...
    '-mk','/absolute/examplefiles/markersfile.txt', ...
    '-refgene','/absolute/refgenefiles/hg16.mat', ...
    '-alf','/absolute/examplefiles/arraylistfile.txt', ...
    '-cnv','/absolute/examplefiles/cnvfile.txt', ...
    '-genegistic','1','-smallmem','1','-broad','1','-brlen','0.5', ...
    '-conf','0.90','-armpeel','1','-savegene','1','-gcm','extreme');
```

Install the Runtime for the **same compiler release**, at the same or newer
update level. Point the new launcher at its direct version directory:

```bash
export GISTIC_MCR_ROOT=/absolute/path/to/MATLAB_Runtime/R2026a
export GISTIC_COMPAT=off
./build/R2026a-candidate/run_gistic_example "$PWD/results/modern-example"
```

Do not point the old executable at a newer Runtime. MathWorks explicitly
requires a [matching Runtime release](https://www.mathworks.com/help/compiler_sdk/ml_code/about-the-matlab-runtime.html).
The launcher reads the ABI file beside a new executable; old official 2.0.23
executables default to ABI 8.3. A direct Runtime root works for both version
naming schemes. An explicit `GISTIC_MCR_ABI` overrides metadata for diagnosis.

Before distributing any candidate, run the scientific comparisons in
[TESTING.md](TESTING.md), including a licensed MATLAB comparison, on both the
build host and an affected AMD compute node. If an API is actually incompatible,
make the smallest change in a separate commit and repeat those comparisons.
Do not preemptively replace `nanmean`, `histc`, sorting, interpolation, `lunique`,
permutation convolutions, or thresholds merely because they are old APIs.

## Packaging and redistribution

The root repository has an MIT license; `support/LICENSE.txt` retains separate
historical distribution terms. Both texts and the existing copyright notices
are preserved and copied into the candidate package. This project does not
resolve that historical inconsistency or grant rights to third-party binaries.
Runtime use/download is available without a MATLAB license; compilation requires
licensed tools. Consult the applicable MathWorks license for redistribution.
No MATLAB Runtime, MEX rebuild, downloaded executable, or proprietary component
is added to Git. Obtain Runtime from MathWorks and retain the installer checksum
and complete release/update identification outside the source repository.

The old `support/release_gistic_source.sh` and installation documents remain as
historical records. Its site-specific SVN/Broad paths, bundled installer and
permissions are not the new build workflow.

## Pinned original-runtime assets

For the same legacy executable used in the tests, download from GenePattern's
pinned revision and check it before making it executable:

```bash
export GISTIC_ASSET_DIR=/absolute/new-gistic-assets
mkdir -p "$GISTIC_ASSET_DIR"
curl -fL --retry 2 \
  https://raw.githubusercontent.com/genepattern/GISTIC_2.0/9455555051a59a2aa095bc84834227622b13bec1/gp_gistic2_from_seg \
  -o "$GISTIC_ASSET_DIR/gp_gistic2_from_seg"
(cd "$GISTIC_ASSET_DIR" && sha256sum -c <<'SUMS'
1045c8372d58b26a8638b703d054e80472bb1527fcf015921344b5f299921576  gp_gistic2_from_seg
SUMS
)
chmod +x "$GISTIC_ASSET_DIR/gp_gistic2_from_seg"
```

Download/install R2014a from the MathWorks link in INVESTIGATION, verifying the
recorded installer SHA-256. The test installation used:

```bash
unzip -q "$GISTIC_ASSET_DIR/MCR_R2014a.zip" -d "$GISTIC_ASSET_DIR/installer"
env -u DISPLAY "$GISTIC_ASSET_DIR/installer/install" \
  -mode silent -agreeToLicense yes \
  -destinationFolder "$GISTIC_ASSET_DIR/mcr" \
  -outputFile "$GISTIC_ASSET_DIR/install.log"
./scripts/prepare_legacy.sh "$GISTIC_ASSET_DIR/gp_gistic2_from_seg" \
  "$GISTIC_ASSET_DIR/mcr/v83" "$GISTIC_ASSET_DIR/candidate"
"$GISTIC_ASSET_DIR/candidate/run_gistic_example" "$GISTIC_ASSET_DIR/example-off"
```

The silent installer invocation accepts MathWorks' license terms. Required OS
libraries still depend on the host. On our Ubuntu 24.04 guest, the real ncurses5
and tinfo5 packages linked/hashed in INVESTIGATION were extracted privately with
`dpkg-deb -x`. Set `GISTIC_EXTRA_LIBRARY_PATH` to that private
`lib/x86_64-linux-gnu` directory if needed. No global library replacement or
ABI-6-to-ABI-5 renaming is involved.
