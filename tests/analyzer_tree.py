import unittest

import onlinejudge_template.analyzer.parser as parser
from onlinejudge_template.types import *


class TestFormatStringAnalyzerAtCoder(unittest.TestCase):
    """TestFormatStringAnalyzerAtCoder is a class for unit tests for the format string analyzer about AtCoder (without network access).
    """
    def test_agc041_a(self) -> None:
        # https://atcoder.jp/contests/agc041/tasks/agc041_a
        format_string = '\n'.join([
            r'<var>N</var> <var>A</var> <var>B</var>',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            ItemNode(name='A'),
            ItemNode(name='B'),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_agc041_b(self) -> None:
        # https://atcoder.jp/contests/agc041/tasks/agc041_b
        format_string = '\n'.join([
            r'<var>N</var> <var>M</var> <var>V</var> <var>P</var>',
            r'<var>A_1</var> <var>A_2</var> <var>...</var> <var>A_N</var>',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            ItemNode(name='M'),
            ItemNode(name='V'),
            ItemNode(name='P'),
            NewlineNode(),
            LoopNode(name='i', size='N', body=ItemNode(name='A', indices=('i + 1', ))),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_arc001_1(self) -> None:
        # https://atcoder.jp/contests/arc001/tasks/arc001_1
        format_string = '\n'.join([
            r'',
            r'<var>N</var>',
            r'<var>c_1c_2c_3…c_N</var>',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            NewlineNode(),
            LoopNode(name='i', size='N', body=ItemNode(name='c', indices=('i + 1', ))),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    @unittest.expectedFailure
    def test_arc001_3(self) -> None:
        # https://atcoder.jp/contests/arc001/tasks/arc001_3
        format_string = '\n'.join([
            r'',
            r'<var>c_{11}</var> <var>c_{12}</var> … <var>c_{18}</var>',
            r'<var>c_{21}</var> <var>c_{22}</var> … <var>c_{28}</var>',
            r':',
            r':',
            r'<var>c_{81}</var> <var>c_{82}</var> … <var>c_{88}</var>',
            r'',
        ]).strip() + '\n'
        format_tree = LoopNode(name='j', size='8', body=SequenceNode(items=[
            LoopNode(name='i', size='8', body=ItemNode(name='c', indices=('i + 1', 'j + 1'))),
            NewlineNode(),
        ]))

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    @unittest.expectedFailure
    def test_arc001_4(self) -> None:
        # https://atcoder.jp/contests/arc001/tasks/arc001_4
        format_string = '\n'.join([
            r'',
            r'<var>N</var>',
            r'<var>start</var> <var>goal</var>',
            r'<var>l_0</var> <var>r_0</var>',
            r'<var>l_1</var> <var>r_1</var>',
            r'<var>:</var>',
            r'<var>:</var>',
            r'<var>l_N</var> <var>r_N</var>',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            NewlineNode(),
            ItemNode(name='start'),
            ItemNode(name='goal'),
            NewlineNode(),
            LoopNode(name='i', size='N + 1', body=SequenceNode(items=[
                ItemNode(name='l', indices=('i', )),
                ItemNode(name='r', indices=('i', )),
                NewlineNode(),
            ])),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_arc066_e(self) -> None:
        # https://atcoder.jp/contests/arc066/tasks/arc066_c
        # https://github.com/online-judge-tools/template-generator/issues/13
        format_string = '\n'.join([
            r'',
            r'<var>N</var>',
            r'<var>A_1</var> <var>op_1</var> <var>A_2</var> <var>...</var> <var>op_{N-1}</var> <var>A_N</var>',
            r'',
        ]).strip() + '\n'

        self.assertRaises(parser.FormatStringParserError, lambda: parser.run(format_string))


class TestFormatStringAnalyzerLibraryChecker(unittest.TestCase):
    """TestFormatStringAnalyzerLibraryChecker is a class for unit tests for the format string analyzer about Library Checker (without network access).
    """
    def test_unionfind(self) -> None:
        # https://judge.yosupo.jp/problem/unionfind
        format_string = '\n'.join([
            r'$N$ $Q$',
            r'$t_1$ $u_1$ $v_1$',
            r'$t_2$ $u_2$ $v_2$',
            r':',
            r'$t_Q$ $u_Q$ $v_Q$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            ItemNode(name='Q'),
            NewlineNode(),
            LoopNode(name='i', size='Q', body=SequenceNode(items=[
                ItemNode(name='t', indices=('i + 1', )),
                ItemNode(name='u', indices=('i + 1', )),
                ItemNode(name='v', indices=('i + 1', )),
                NewlineNode(),
            ])),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_input_two_edge_connected_components(self) -> None:
        # https://judge.yosupo.jp/problem/two_edge_connected_components
        format_string = '\n'.join([
            r'$N$ $M$',
            r'$a_0$ $b_0$',
            r'$a_1$ $b_1$',
            r':',
            r'$a_{M - 1}$ $b_{M - 1}$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            ItemNode(name='M'),
            NewlineNode(),
            LoopNode(name='i', size='M', body=SequenceNode(items=[
                ItemNode(name='a', indices=('i', )),
                ItemNode(name='b', indices=('i', )),
                NewlineNode(),
            ])),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_output_two_edge_connected_components(self) -> None:
        # https://judge.yosupo.jp/problem/two_edge_connected_components
        format_string = '\n'.join([
            r'$l$ $v_0$ $v_1$ ... $v_{l-1}$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='l'),
            LoopNode(name='i', size='l', body=ItemNode(name='v', indices=('i', ))),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_input_stirling_number_of_the_second_kind(self) -> None:
        # https://judge.yosupo.jp/problem/stirling_number_of_the_second_kind
        format_string = '\n'.join([
            r'$N$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    @unittest.expectedFailure
    def test_output_stirling_number_of_the_second_kind(self) -> None:
        # https://judge.yosupo.jp/problem/stirling_number_of_the_second_kind
        format_string = '\n'.join([
            r'$S(N, 0)$ $\cdots$ $S(N, N)$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='l'),
            LoopNode(name='i', size='l', body=SequenceNode(items=[
                ItemNode(name='v', indices=('i', )),
                NewlineNode(),
            ])),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))


class TestFormatStringAnalyzerYukicoder(unittest.TestCase):
    """TestFormatStringAnalyzerYukicoder is a class for unit tests for the format string analyzer about yukicoder (without network access).
    """
    def test_no_1000(self) -> None:
        # https://yukicoder.me/problems/no/1000
        format_string = '\n'.join([
            r'$N\ Q$',
            r'$A_1\ A_2\ \cdots \ A_N$',
            r'$c_1\ x_1\ y_1$',
            r'$c_2\ x_2\ y_2$',
            r'$\vdots$',
            r'$c_Q\ x_Q\ y_Q$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            ItemNode(name='Q'),
            NewlineNode(),
            LoopNode(name='i', size='N', body=ItemNode(name='A', indices=('i + 1', ))),
            NewlineNode(),
            LoopNode(name='i', size='Q', body=SequenceNode(items=[
                ItemNode(name='c', indices=('i + 1', )),
                ItemNode(name='x', indices=('i + 1', )),
                ItemNode(name='y', indices=('i + 1', )),
                NewlineNode(),
            ])),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_no_999(self) -> None:
        # https://yukicoder.me/problems/no/999
        format_string = '\n'.join([
            r'$N$',
            r'$A_1\ A_2\ \cdots \ A_{2N}$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            NewlineNode(),
            LoopNode(name='i', size='2 * N', body=ItemNode(name='A', indices=('i + 1', ))),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_no_100(self) -> None:
        # https://yukicoder.me/problems/no/100
        format_string = '\n'.join([
            r'$N$',
            r'$a_1$ $\ldots$ $a_N$',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            NewlineNode(),
            LoopNode(name='i', size='N', body=ItemNode(name='a', indices=('i + 1', ))),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_no_1(self) -> None:
        """The problem https://yukicoder.me/problems/no/1 uses `\\(` and `\\)` for TeX.
        """

        format_string = '\n'.join([
            r'\(N\)',
            r'\(C\)',
            r'\(V\)',
            r'\(S_1\ S_2\ S_3\ \dots\ S_V\)',
            r'\(T_1\ T_2\ T_3\ \dots\ T_V\)',
            r'\(Y_1\ Y_2\ Y_3\ \dots\ Y_V\)',
            r'\(M_1\ M_2\ M_3\ \dots\ M_V\)',
            r'',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='N'),
            NewlineNode(),
            ItemNode(name='C'),
            NewlineNode(),
            ItemNode(name='V'),
            NewlineNode(),
            LoopNode(name='i', size='V', body=ItemNode(name='S', indices=('i + 1', ))),
            NewlineNode(),
            LoopNode(name='i', size='V', body=ItemNode(name='T', indices=('i + 1', ))),
            NewlineNode(),
            LoopNode(name='i', size='V', body=ItemNode(name='Y', indices=('i + 1', ))),
            NewlineNode(),
            LoopNode(name='i', size='V', body=ItemNode(name='M', indices=('i + 1', ))),
            NewlineNode(),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))

    def test_no_1172(self) -> None:
        """The problem https://yukicoder.me/problems/no/1172 uses `\\quad` for spacing.
        """

        format_string = '\n'.join([
            r'$K \quad N \quad M$',
            r'$a_0 \quad a_1 \quad \cdots \quad a_{K-1}$',
            r'$c_1 \quad c_2 \quad \cdots \quad c_K$',
            r'$l_1 \quad r_1$',
            r'$l_2 \quad r_2$',
            r'$\ \vdots$',
            r'$l_M \quad r_M$',
        ]).strip() + '\n'
        format_tree = SequenceNode(items=[
            ItemNode(name='K'),
            ItemNode(name='N'),
            ItemNode(name='M'),
            NewlineNode(),
            LoopNode(name='i', size='K', body=ItemNode(name='a', indices=('i', ))),
            NewlineNode(),
            LoopNode(name='i', size='K', body=ItemNode(name='c', indices=('i + 1', ))),
            NewlineNode(),
            LoopNode(name='i', size='M', body=SequenceNode(items=[
                ItemNode(name='l', indices=('i + 1', )),
                ItemNode(name='r', indices=('i + 1', )),
                NewlineNode(),
            ])),
        ])

        self.assertEqual(str(parser.run(format_string)), str(format_tree))
