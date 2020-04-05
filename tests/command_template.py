import contextlib
import io
import pathlib
import subprocess
import sys
import tempfile
import textwrap
import unittest
from typing import *

from onlinejudge_template.main import main


class TestOJTemplateCommand(unittest.TestCase):
    def _helper(self, *, url: str, template: str, placeholder: str, code: str, compile: Callable[[pathlib.Path], str], command: Callable[[pathlib.Path], str]):
        with tempfile.TemporaryDirectory() as tmpdir_:
            tmpdir = pathlib.Path(tmpdir_)
            source_file = tmpdir / template
            test_directory = tmpdir / 'test'

            # generate
            fh = io.TextIOWrapper(io.BytesIO(), write_through=True)
            with contextlib.redirect_stdout(fh):
                main(['-t', template, url])
            code = fh.buffer.getvalue().decode().replace(placeholder, code, 1)
            print(code)
            with open(source_file, 'w') as fh:
                fh.write(code)

            # test
            subprocess.check_call(compile(tmpdir), stdout=sys.stdout, stderr=sys.stderr)
            subprocess.check_call(['oj', 'd', '--directory', str(test_directory), url], stdout=sys.stdout, stderr=sys.stderr)
            subprocess.check_call(['oj', 't', '--directory', str(test_directory), '-c', command(tmpdir)], stdout=sys.stdout, stderr=sys.stderr)

    def test_main_py_abc152_b(self) -> None:
        url = 'https://atcoder.jp/contests/abc152/tasks/abc152_b'
        template = 'main.py'
        placeholder = '    pass  # TODO: edit here\n'
        code = textwrap.indent(textwrap.dedent("""\
            x = str(a) * b
            y = str(b) * a
            return int(min(x, y))
        """), '    ')
        compile = lambda tmpdir: [sys.executable, '--version']
        command = lambda tmpdir: ' '.join([sys.executable, str(tmpdir / 'main.py')])
        self._helper(url=url, template=template, placeholder=placeholder, code=code, compile=compile, command=command)

    def test_main_cpp_aplusb(self) -> None:
        url = 'https://judge.yosupo.jp/problem/aplusb'
        template = 'main.cpp'
        placeholder = '    // TODO: edit here\n'
        code = textwrap.indent(textwrap.dedent("""\
            return A + B;
        """), '    ')
        compile = lambda tmpdir: ['g++', '-std=c++14', str(tmpdir / 'main.cpp'), '-o', str(tmpdir / 'a.out')]
        command = lambda tmpdir: str(tmpdir / 'a.out')
        self._helper(url=url, template=template, placeholder=placeholder, code=code, compile=compile, command=command)
