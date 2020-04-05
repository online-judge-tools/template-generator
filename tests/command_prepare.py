import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from typing import *

from onlinejudge_prepare.main import chdir, main


class TestOJPrepareCommand(unittest.TestCase):
    def _helper(self, *, url: str, subdir: str, template: str, placeholder: str, code: str, compile: Callable[[pathlib.Path], str], command: Callable[[pathlib.Path], str]):
        with tempfile.TemporaryDirectory() as tmpdir_:
            tmpdir = pathlib.Path(tmpdir_)
            with chdir(tmpdir):
                config_file = tmpdir / 'config.toml'
                source_file = tmpdir / subdir / template
                test_directory = tmpdir / subdir / 'test'

                # prepare
                with open(config_file, 'w') as fh:
                    pass
                main(['--config-file', str(config_file), url])

                # edit code
                with open(source_file) as fh:
                    code = fh.read().replace(placeholder, code, 1)
                print(code)
                with open(source_file, 'w') as fh:
                    fh.write(code)

                # test
                subprocess.check_call(compile(tmpdir), stdout=sys.stdout, stderr=sys.stderr)
                subprocess.check_call(['oj', 't', '--directory', str(test_directory), '-c', command(tmpdir)], stdout=sys.stdout, stderr=sys.stderr)

    def test_main_py_contest_abc125_a(self) -> None:
        url = 'https://atcoder.jp/contests/abc125'
        subdir = 'abc125_a'
        template = 'main.cpp'
        placeholder = '    // TODO: edit here\n'
        code = textwrap.indent(textwrap.dedent("""\
            return T / A * B;
        """), '    ')
        compile = lambda tmpdir: ['g++', '-std=c++14', str(tmpdir / subdir / 'main.cpp'), '-o', str(tmpdir / 'a.out')]
        command = lambda tmpdir: str(tmpdir / 'a.out')
        self._helper(url=url, subdir=subdir, template=template, placeholder=placeholder, code=code, compile=compile, command=command)

    def test_main_cpp_problem_yuki_993(self) -> None:
        url = 'https://yukicoder.me/problems/no/993'
        subdir = '.'
        template = 'main.py'
        placeholder = '    # TODO: edit here\n'
        code = textwrap.indent(textwrap.dedent("""\
            return S.replace('ao', 'ki')
        """), '    ')
        compile = lambda tmpdir: [sys.executable, '--version']
        command = lambda tmpdir: ' '.join([sys.executable, str(tmpdir / subdir / 'main.py')])
        self._helper(url=url, subdir=subdir, template=template, placeholder=placeholder, code=code, compile=compile, command=command)
