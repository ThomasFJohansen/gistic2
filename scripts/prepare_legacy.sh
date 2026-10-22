#!/usr/bin/env bash
set -euo pipefail
[[ $# == 3 ]] || { echo "usage: $0 ORIGINAL_EXECUTABLE DIRECT_RUNTIME_ROOT NEW_DIRECTORY" >&2; exit 2; }
repo=$(dirname -- "$(dirname -- "$(readlink -f -- "$0")")")
exe=$(readlink -f -- "$1")
runtime=$(readlink -f -- "$2")
[[ -x $exe && -f $runtime/runtime/glnxa64/libmwmclmcrrt.so.8.3 ]] || { echo 'need executable and R2014a Runtime 8.3' >&2; exit 2; }
if [[ $(sha256sum -- "$exe" | cut -d' ' -f1) == 576196ec20117e0543cb3948ed4149348b496ce6cccc83094a331487ddb4f821 ]]; then
    echo 'The checked-in executable requires MCR 7.14. Supply the official 2.0.23 R2014a executable.' >&2; exit 2
fi
[[ ! -e $3 ]] || { echo "refusing existing directory: $3" >&2; exit 2; }
mkdir -p -- "$3"
cp -- "$repo/support/gistic2" "$repo/support/run_gistic_example" "$3/"
ln -s -- "$exe" "$3/gp_gistic2_from_seg"
ln -s -- "$runtime" "$3/MATLAB_Compiler_Runtime"
ln -s -- "$repo/support/examplefiles" "$3/examplefiles"
ln -s -- "$repo/support/refgenefiles" "$3/refgenefiles"
chmod +x "$3/gistic2" "$3/run_gistic_example"
