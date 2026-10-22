#!/usr/bin/env python3
"""Serial, fresh-cache GISTIC experiments. Exit zero alone is NOT a scientific pass."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import time
from compare_outputs import compare, validate

REPO = Path(__file__).resolve().parents[1]
CONTROL = '''OMP_NUM_THREADS MKL_NUM_THREADS OPENBLAS_NUM_THREADS MKL_CBWR MATLAB_DISABLE_CBWR
MKL_DEBUG_CPU_TYPE OMP_THREAD_LIMIT MKL_DOMAIN_NUM_THREADS MKL_DYNAMIC OMP_DYNAMIC
GOMP_CPU_AFFINITY KMP_AFFINITY OMP_PROC_BIND GISTIC_CPU GISTIC_COMPAT GISTIC_INHERIT_LIBRARY_ENV
LD_LIBRARY_PATH LD_PRELOAD BLAS_VERSION LAPACK_VERSION MATLABPATH MATLAB_JAVA DISPLAY'''.split()

def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')

def snapshot(pid, executable=None, output=None):
    result = {'popen_pid': pid}
    # Some sandbox hosts expose a /proc mount from a different PID namespace.
    # Locate only the exact executable and unique output argv, never guess a PID.
    if executable is not None and output is not None:
        matches = []
        for path in Path('/proc').glob('[0-9]*/cmdline'):
            try:
                argv = path.read_bytes().split(b'\0')
                if argv and argv[0] == os.fsencode(executable) and os.fsencode(output) in argv:
                    matches.append(int(path.parent.name))
            except OSError:
                pass
        if len(matches) == 1:
            pid = matches[0]
        result['matching_proc_pids'] = matches
    result['inspected_pid'] = pid
    for name in ('status', 'maps'):
        try:
            data = Path(f'/proc/{pid}/{name}').read_text()
            if name == 'status':
                result[name] = '\n'.join(x for x in data.splitlines()
                                          if x.startswith(('Name:', 'State:', 'Threads:', 'Cpus_allowed_list:')))
            else:
                result[name] = sorted(set(x.split()[-1] for x in data.splitlines()
                                          if any(s in x.lower() for s in ('mkl', 'blas', 'lapack', 'libmw', 'libgomp', 'libiomp'))))
        except OSError as exc:
            result[name+'_unavailable'] = str(exc)
    return result

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--runtime', type=Path, required=True, help='direct versioned Runtime root')
    p.add_argument('--executable', type=Path, required=True)
    p.add_argument('--launcher', type=Path, default=REPO/'support/gistic2')
    p.add_argument('--original-launcher', type=Path, help='original launcher in correctly configured original installation')
    p.add_argument('--output', type=Path, required=True, help='new output directory, preferably local disk')
    p.add_argument('--baseline', type=Path, help='independently trusted output for the exact same input/options')
    p.add_argument('--cases', nargs='+', choices=['original','off','threads','affinity','single','sse42','debug4'], default=['off','threads','affinity','single'])
    p.add_argument('--experimental-mkl', action='store_true')
    p.add_argument('--repeats', type=int, default=2)
    p.add_argument('--timeout', type=int, default=1800)
    p.add_argument('--profile', choices=['official','genepattern'], default='official')
    p.add_argument('--args-json', type=Path, help='custom JSON array of CLI strings, excluding -b')
    a = p.parse_args()
    if a.repeats < 1 or a.timeout < 1:
        p.error('repeats and timeout must be positive')
    for attr in ('runtime','executable','launcher','output','baseline','original_launcher'):
        value = getattr(a, attr)
        if value is not None:
            setattr(a, attr, value.resolve())
    cases = list(dict.fromkeys(a.cases + (['sse42','debug4'] if a.experimental_mkl else [])))
    if 'original' in cases and not a.original_launcher:
        p.error('original requires --original-launcher')
    if a.baseline and validate(a.baseline):
        p.error('baseline failed output completeness validation')
    example = REPO/'support/examplefiles'
    inputs = [example/'segmentationfile.txt', example/'markersfile.txt', REPO/'support/refgenefiles/hg16.mat', example/'arraylistfile.txt', example/'cnvfile.txt']
    args = [item for pair in zip(['-seg','-mk','-refgene','-alf','-cnv'], map(str, inputs)) for item in pair]
    args += ['-genegistic','1','-smallmem','1','-broad','1','-brlen','0.5','-conf','0.90','-armpeel','1','-savegene','1','-gcm','extreme']
    if a.profile == 'genepattern':
        args[args.index('-broad')+1] = '0'
        args[args.index('-armpeel')+1] = '0'
        args += ['-js','4','-genepattern','1','-saveseg','0','-savedata','0']
    if a.args_json:
        args = json.loads(a.args_json.read_text())
        if not isinstance(args, list) or not all(isinstance(x,str) for x in args) or '-b' in args:
            p.error('--args-json must contain strings and omit -b')
        inputs = [Path(args[i+1]) for i,x in enumerate(args[:-1]) if x in ('-seg','-mk','-refgene','-alf','-cnv')]
    a.output.mkdir(parents=True, exist_ok=False)
    env = os.environ.copy()
    for key in CONTROL:
        env.pop(key, None)
    env.update(GISTIC_EXECUTABLE=str(a.executable), GISTIC_MCR_ROOT=str(a.runtime), GISTIC_HEADLESS='1', LC_ALL='C')
    provenance = {'date_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
                  'physical_cpu_verified': False, 'affinity': sorted(os.sched_getaffinity(0)),
                  'argv': args, 'profile': 'custom' if a.args_json else a.profile,
                  'baseline': str(a.baseline) if a.baseline else 'first complete run; internal consistency only',
                  'hashes': {str(x): sha(x) for x in [a.executable,a.launcher,*inputs]},
                  'extra_library_path': env.get('GISTIC_EXTRA_LIBRARY_PATH',''),
                  'conditions': 'serial; fresh MCR cache for every run; inherited thread/dispatch/library overrides cleared'}
    if a.original_launcher:
        provenance['hashes'][str(a.original_launcher)] = sha(a.original_launcher)
    for name, cmd in {'lscpu':['lscpu'], 'uname':['uname','-a'], 'glibc':['ldd','--version']}.items():
        provenance[name] = subprocess.run(cmd,capture_output=True,text=True).stdout
    for name in ('/proc/cpuinfo','/etc/os-release','/sys/fs/cgroup/cpu.max'):
        try: provenance[name] = Path(name).read_text()
        except OSError as exc: provenance[name] = str(exc)
    provenance['runtime_hashes'] = {str(x): sha(x) for x in (a.runtime/'runtime/glnxa64').glob('libmwmclmcrrt.so.*')}
    write(a.output/'environment.json', provenance)
    resource.setrlimit(resource.RLIMIT_CORE, (0,0))
    results = []
    reference = a.baseline
    for repeat in range(1, a.repeats+1):
        for case in cases:
            run = a.output/f'{repeat:02d}-{case}'
            out = run/'outputs'
            out.mkdir(parents=True)
            cache = run/'mcr-cache'
            cache.mkdir()
            run_env = env.copy()
            run_env.update(MCR_CACHE_ROOT=str(cache), GISTIC_COMPAT=case if case in ('off','threads','affinity','single') else 'off')
            if case == 'sse42':
                run_env.update(MATLAB_DISABLE_CBWR='1', MKL_CBWR='SSE4_2')
            if case == 'debug4':
                run_env['MKL_DEBUG_CPU_TYPE'] = '4'
            launcher = a.original_launcher if case == 'original' else a.launcher
            if case == 'original':
                run_env['LD_LIBRARY_PATH'] = run_env.get('GISTIC_EXTRA_LIBRARY_PATH','')
            cmd = [str(launcher),'-b',str(out),*args]
            before = resource.getrusage(resource.RUSAGE_CHILDREN)
            start = time.monotonic()
            timed_out = False
            samples = []
            with (run/'run.log').open('w') as log:
                proc = subprocess.Popen(cmd,env=run_env,cwd=launcher.parent,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
                try:
                    while proc.poll() is None:
                        elapsed = time.monotonic()-start
                        if len(samples) < 3 and elapsed >= (len(samples)+1)*10:
                            samples.append(snapshot(proc.pid, a.executable, out))
                        if elapsed > a.timeout:
                            timed_out = True
                            os.killpg(proc.pid,signal.SIGTERM)
                            try: proc.wait(timeout=5)
                            except subprocess.TimeoutExpired:
                                os.killpg(proc.pid,signal.SIGKILL)
                            break
                        time.sleep(1)
                    proc.wait()
                except BaseException:
                    if proc.poll() is None:
                        os.killpg(proc.pid,signal.SIGTERM)
                        try: proc.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            os.killpg(proc.pid,signal.SIGKILL)
                            proc.wait()
                    raise
            after = resource.getrusage(resource.RUSAGE_CHILDREN)
            result = {'case':case,'repeat':repeat,'returncode':proc.returncode,'timeout':timed_out,
                      'wall_seconds':time.monotonic()-start,
                      'cpu_seconds':after.ru_utime+after.ru_stime-before.ru_utime-before.ru_stime,
                      'argv':cmd, 'process_samples':samples, 'validation_errors':validate(out)}
            complete = proc.returncode == 0 and not timed_out and not result['validation_errors']
            if complete:
                if reference is None:
                    reference = out
                result['comparison'] = compare(reference,out)
                result['status'] = 'match' if result['comparison']['equal'] else 'difference'
            else:
                result['status'] = 'failed'
            result['output_sha256'] = {x.name:sha(x) for x in out.iterdir() if x.is_file()}
            write(run/'result.json',result)
            results.append(result)
            write(a.output/'summary.json',results)
            print(json.dumps({k:result[k] for k in ('case','repeat','status','returncode','wall_seconds','cpu_seconds','validation_errors')}),flush=True)
    return 0 if all(x['status']=='match' for x in results) else 1

if __name__ == '__main__':
    raise SystemExit(main())
