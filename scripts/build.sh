#!/usr/bin/env bash
# Requires a licensed modern MATLAB, MATLAB Compiler, Statistics Toolbox, and supported C compiler.
set -euo pipefail
[[ $# == 1 ]] || { echo "usage: $0 NEW_BUILD_DIRECTORY" >&2; exit 2; }
repo=$(dirname -- "$(dirname -- "$(readlink -f -- "$0")")")
matlab=${MATLAB_BIN:-matlab}
command -v "$matlab" >/dev/null || { echo 'MATLAB_BIN must identify licensed MATLAB (not Runtime)' >&2; exit 2; }
[[ -f $repo/snputil/@SegArray/cosort.c ]] || { echo 'run git submodule update --init --recursive' >&2; exit 2; }
[[ ! -e $1 ]] || { echo "refusing existing output: $1" >&2; exit 2; }
mkdir -p -- "$1"
export GISTIC_BUILD_OUTPUT=$(readlink -f -- "$1")
export GISTIC_BUILD_REPO=$repo
{
    git -C "$repo" rev-parse HEAD
    git -C "$repo" submodule status --recursive
    git -C "$repo" status --short
    git -C "$repo" diff --submodule=diff
} > "$GISTIC_BUILD_OUTPUT/source-provenance.txt"
"$matlab" -batch "addpath(fullfile(getenv('GISTIC_BUILD_REPO'),'scripts')); build_gistic"
cp -- "$repo/support/gistic2" "$repo/support/run_gistic_example" "$GISTIC_BUILD_OUTPUT/"
cp -R -- "$repo/support/examplefiles" "$repo/support/refgenefiles" "$GISTIC_BUILD_OUTPUT/"
cp -- "$repo/LICENSE" "$GISTIC_BUILD_OUTPUT/LICENSE.source"
cp -- "$repo/support/LICENSE.txt" "$GISTIC_BUILD_OUTPUT/LICENSE.distribution"
chmod +x "$GISTIC_BUILD_OUTPUT/gistic2" "$GISTIC_BUILD_OUTPUT/run_gistic_example"
sha256sum "$GISTIC_BUILD_OUTPUT/gp_gistic2_from_seg" > "$GISTIC_BUILD_OUTPUT/executable.sha256"
echo 'Build complete. Numerical regression and target-host validation are still required.'
