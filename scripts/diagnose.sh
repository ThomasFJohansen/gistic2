#!/usr/bin/env bash
# Read-only. Review paths/host information before sharing the output.
set -uo pipefail
for cmd in 'lscpu' 'cat /proc/cpuinfo' 'uname -a' 'ldd --version' 'cat /etc/os-release'; do
    printf '\n$ %s\n' "$cmd"
    bash -c "$cmd"
done
printf '\nCPU allocation\n'
awk '/Cpus_allowed|Mems_allowed/ {print}' /proc/self/status
cat /sys/fs/cgroup/cpu.max 2>/dev/null || true
printf '\nSelected environment\n'
for var in GISTIC_COMPAT GISTIC_CPU GISTIC_MCR_ROOT GISTIC_EXECUTABLE GISTIC_MCR_ABI GISTIC_EXTRA_LIBRARY_PATH GISTIC_INHERIT_LIBRARY_ENV OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS MKL_CBWR MATLAB_DISABLE_CBWR MKL_DEBUG_CPU_TYPE BLAS_VERSION LAPACK_VERSION LD_LIBRARY_PATH LD_PRELOAD DISPLAY SLURM_JOB_ID SLURM_CPUS_PER_TASK; do
    printf '%s=%s\n' "$var" "${!var-<unset>}"
done
if [[ -n ${GISTIC_EXECUTABLE:-} ]]; then
    sha256sum -- "$GISTIC_EXECUTABLE"
    readelf -d -- "$GISTIC_EXECUTABLE" 2>/dev/null || true
fi
printf '\nGuest CPU information does not establish physical processor identity.\n'
