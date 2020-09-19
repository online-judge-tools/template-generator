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
    """TestOJTemplateCommand is a class for end-to-end tests about oj-template command.
    The tests actually compile and execute the generated code and check them get AC on sample cases.
    """
    def _helper(self, *, url: str, template: str, placeholder: str, code: str, compile: Callable[[pathlib.Path], List[str]], command: Callable[[pathlib.Path], str]):
        with tempfile.TemporaryDirectory() as tmpdir_:
            tmpdir = pathlib.Path(tmpdir_)
            source_file = tmpdir / template
            test_directory = tmpdir / 'test'

            # generate
            fh: IO = io.TextIOWrapper(io.BytesIO(), write_through=True)
            with contextlib.redirect_stdout(fh):
                main(['-t', template, url])
            code: str = fh.buffer.getvalue().decode().replace(placeholder, code, 1)  # type: ignore
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
        placeholder = '    pass  # TODO: edit here'
        code = textwrap.indent(textwrap.dedent("""\
            x = str(a) * b
            y = str(b) * a
            return int(min(x, y))
        """), '    ')
        compile = lambda tmpdir: [sys.executable, '--version']  # nop
        command = lambda tmpdir: ' '.join([sys.executable, str(tmpdir / template)])
        self._helper(url=url, template=template, placeholder=placeholder, code=code, compile=compile, command=command)

    def test_main_cpp_aplusb(self) -> None:
        url = 'https://judge.yosupo.jp/problem/aplusb'
        template = 'main.cpp'
        placeholder = '    // TODO: edit here'
        code = textwrap.indent(textwrap.dedent("""\
            return A + B;
        """), '    ')
        compile = lambda tmpdir: ['g++', '-std=c++14', str(tmpdir / template), '-o', str(tmpdir / 'a.out')]
        command = lambda tmpdir: str(tmpdir / 'a.out')
        self._helper(url=url, template=template, placeholder=placeholder, code=code, compile=compile, command=command)


class TestOJTemplateCommandGenerator(unittest.TestCase):
    """TestOJTemplateCommandGenerator is a class for end-to-end tests about oj-template command.
    The tests actually executes the generator and check the result with a validator.
    """
    def _helper(self, *, url: str, template: str, compile: Callable[[pathlib.Path], List[str]], command: Callable[[pathlib.Path], List[str]]):
        with tempfile.TemporaryDirectory() as tmpdir_:
            tmpdir = pathlib.Path(tmpdir_)
            source_file = tmpdir / template

            # generate
            with open(source_file, 'w') as fh:
                with contextlib.redirect_stdout(fh):
                    main(['-t', template, url])

            # test
            subprocess.check_call(compile(tmpdir), stdout=sys.stdout, stderr=sys.stderr)
            return subprocess.check_output(command(tmpdir), stderr=sys.stderr)

    def test_generate_py_arc088_b(self) -> None:
        # arc088_b has a format with a binary string variable.
        url = 'https://atcoder.jp/contests/arc088/tasks/arc088_b'
        template = 'generate.py'
        compile = lambda tmpdir: [sys.executable, '--version']  # nop
        command = lambda tmpdir: [sys.executable, str(tmpdir / template)]

        def validate(case: bytes) -> None:
            lines = case.splitlines()
            self.assertEqual(len(lines), 1)
            s, = lines[0].split()
            self.assertTrue(s.isalpha())

        validate(self._helper(url=url, template=template, compile=compile, command=command))

    def test_generate_py_arc089_b(self) -> None:
        # arc089_b has a non-trivial format with char variables.
        url = 'https://atcoder.jp/contests/arc089/tasks/arc089_b'
        template = 'generate.py'
        compile = lambda tmpdir: [sys.executable, '--version']  # nop
        command = lambda tmpdir: [sys.executable, str(tmpdir / template)]

        def validate(case: bytes) -> None:
            lines = case.splitlines()
            n, k = map(int, lines[0].split())
            self.assertEqual(len(lines) - 1, n)
            for line in lines[1:]:
                x, y, c = line.split()
                int(x)
                int(y)
                self.assertTrue(c.isalpha())
                self.assertEqual(len(c), 1)

        validate(self._helper(url=url, template=template, compile=compile, command=command))
