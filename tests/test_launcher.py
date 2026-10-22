import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

LAUNCHER = Path(__file__).resolve().parents[1]/'support/gistic2'
VARS = ['OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_CBWR',
        'MATLAB_DISABLE_CBWR','MKL_DEBUG_CPU_TYPE','LD_LIBRARY_PATH','LD_PRELOAD',
        'BLAS_VERSION','LAPACK_VERSION','MATLABPATH','MATLAB_JAVA','DISPLAY','XAPPLRESDIR']

class Launcher(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='gistic test ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.runtime = self.root/'runtime space'
        for name in ('runtime/glnxa64','bin/glnxa64','sys/os/glnxa64'):
            (self.runtime/name).mkdir(parents=True)
        (self.runtime/'runtime/glnxa64/libmwmclmcrrt.so.8.3').touch()
        self.exe = self.root/'stub executable'
        self.exe.write_text('#!/usr/bin/python3\nimport os,sys,json\nprint(json.dumps({"argv":sys.argv[1:],"env":{k:os.environ.get(k) for k in '+repr(VARS)+'},"affinity":sorted(os.sched_getaffinity(0)),"cwd":os.getcwd()}))\nsys.exit(int(os.environ.get("STUB_EXIT",0)))\n')
        self.exe.chmod(0o755)
        self.env = {k:v for k,v in os.environ.items() if k not in VARS and not k.startswith('GISTIC_')}
        self.env.update(GISTIC_EXECUTABLE=str(self.exe),GISTIC_MCR_ROOT=str(self.runtime))

    def run_stub(self,args=(),extra=None,prefix=(),ok=True):
        env=self.env.copy(); env.update(extra or {})
        p=subprocess.run([*prefix,str(LAUNCHER),*args],env=env,cwd=self.root,text=True,capture_output=True)
        if ok:
            self.assertEqual(p.returncode,0,p.stderr)
            return json.loads(p.stdout)
        self.assertEqual(p.returncode,2,p.stderr)
        return p

    def test_arguments_and_cwd(self):
        args=['a b','','$(touch should-not-exist)','; hello','*']
        value=self.run_stub(args)
        self.assertEqual(value['argv'],args)
        self.assertEqual(value['cwd'],str(self.root))
        self.assertFalse((self.root/'should-not-exist').exists())

    def test_off_preserves_threads_affinity(self):
        v=self.run_stub(extra={'OMP_NUM_THREADS':'3','MKL_NUM_THREADS':'2'})
        self.assertEqual(v['affinity'],sorted(os.sched_getaffinity(0)))
        self.assertEqual(v['env']['OMP_NUM_THREADS'],'3')
        self.assertEqual(v['env']['MKL_NUM_THREADS'],'2')

    def test_threads_only(self):
        v=self.run_stub(extra={'GISTIC_COMPAT':'threads'})
        self.assertEqual(v['affinity'],sorted(os.sched_getaffinity(0)))
        for key in VARS[:3]: self.assertEqual(v['env'][key],'1')

    @unittest.skipUnless(shutil.which('taskset'),'taskset unavailable')
    def test_respects_restricted_cpuset(self):
        cpu=max(os.sched_getaffinity(0))
        for mode in ('affinity','single'):
            with self.subTest(mode=mode):
                v=self.run_stub(extra={'GISTIC_COMPAT':mode,'OMP_NUM_THREADS':'3'},prefix=['taskset','-c',str(cpu)])
                self.assertEqual(v['affinity'],[cpu])
                self.assertEqual(v['env']['OMP_NUM_THREADS'],'1' if mode=='single' else '3')

    def test_invalid_options(self):
        for extra in ({'GISTIC_COMPAT':'auto'},{'GISTIC_CPU':'0'},
                      {'GISTIC_COMPAT':'single','GISTIC_CPU':'08'},
                      {'GISTIC_COMPAT':'single','GISTIC_CPU':'$(id)'},
                      {'GISTIC_COMPAT':'single','GISTIC_CPU':'999999'},
                      {'GISTIC_MCR_ABI':'../../foo'}, {'GISTIC_HEADLESS':'maybe'},
                      {'GISTIC_INHERIT_LIBRARY_ENV':'yes'}):
            with self.subTest(extra=extra): self.run_stub(extra=extra,ok=False)

    def test_library_isolation(self):
        v=self.run_stub(extra={'LD_LIBRARY_PATH':'/tmp','BLAS_VERSION':'untrusted.so','MATLABPATH':'/tmp'})
        self.assertIsNone(v['env']['BLAS_VERSION'])
        self.assertIsNone(v['env']['MATLABPATH'])
        self.assertNotIn('/tmp',v['env']['LD_LIBRARY_PATH'].split(':'))
        self.assertNotIn('',v['env']['LD_LIBRARY_PATH'].split(':'))

    def test_explicit_inherit_headless(self):
        v=self.run_stub(extra={'GISTIC_INHERIT_LIBRARY_ENV':'1','LD_LIBRARY_PATH':':/tmp:','BLAS_VERSION':'chosen.so','DISPLAY':':88','GISTIC_HEADLESS':'0'})
        self.assertEqual(v['env']['BLAS_VERSION'],'chosen.so')
        self.assertEqual(v['env']['DISPLAY'],':88')
        self.assertIn('/tmp',v['env']['LD_LIBRARY_PATH'].split(':'))
        self.assertNotIn('',v['env']['LD_LIBRARY_PATH'].split(':'))

    def test_extra_library_path_validation(self):
        for value in ('relative','/path/that/does/not/exist'):
            self.run_stub(extra={'GISTIC_EXTRA_LIBRARY_PATH':value},ok=False)
        v=self.run_stub(extra={'GISTIC_EXTRA_LIBRARY_PATH':'/tmp'})
        self.assertTrue(v['env']['LD_LIBRARY_PATH'].endswith(':/tmp'))

    def test_parent_root(self):
        parent=self.root/'parent'; parent.mkdir()
        (parent/'v83').symlink_to(self.runtime,target_is_directory=True)
        v=self.run_stub(extra={'GISTIC_MCR_ROOT':str(parent)})
        self.assertEqual(v['env']['XAPPLRESDIR'],str(self.runtime/'X11/app-defaults'))

    def test_missing_runtime(self):
        self.run_stub(extra={'GISTIC_MCR_ABI':'9.0'},ok=False)

    def test_exit_status(self):
        env=self.env.copy(); env['STUB_EXIT']='37'
        p=subprocess.run([str(LAUNCHER)],env=env,capture_output=True)
        self.assertEqual(p.returncode,37)

    def test_no_implicit_mkl_override(self):
        v=self.run_stub()
        for key in VARS[3:6]: self.assertIsNone(v['env'][key])
        v=self.run_stub(extra={'MKL_CBWR':'SSE4_2','MATLAB_DISABLE_CBWR':'1'})
        self.assertEqual(v['env']['MKL_CBWR'],'SSE4_2')

    def test_missing_taskset(self):
        bindir=self.root/'bin'; bindir.mkdir()
        for name in ('bash','readlink','dirname'):
            (bindir/name).symlink_to(shutil.which(name))
        self.run_stub(extra={'PATH':str(bindir),'GISTIC_COMPAT':'single'},ok=False)
        self.run_stub(extra={'PATH':str(bindir),'GISTIC_COMPAT':'threads'})
