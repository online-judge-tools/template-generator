import textwrap
import unittest

import onlinejudge_template.analyzer.minimum_tree as analyzer
from onlinejudge_template.types import *


class TestMinimumTree(unittest.TestCase):
    def test_simple(self) -> None:
        instances = [
            textwrap.dedent("""\
            3
            1 2
            3 4 1 2
            2 4 1
            """),
            textwrap.dedent("""\
            1
            2 0 8
            """),
        ]
        expected = SequenceNode(items=[
            ItemNode(name='a'),
            NewlineNode(),
            LoopNode(size='a', name='i', body=SequenceNode(items=[
                ItemNode(name='b', indices=['i']),
                LoopNode(size='b_i', name='j', body=ItemNode(name='c', indices=['i', 'j'])),
                NewlineNode(),
            ])),
        ])

        actual = analyzer.construct_minimum_input_format_tree(instances=instances)
        self.assertEqual(str(actual), str(expected))

    def test_codeforces_1406_A(self) -> None:
        """It has only one sample input with multiple cases. Each case is simple.
        """
        # https://codeforces.com/contest/1406/problem/A
        instances = [
            textwrap.dedent("""\
            4
            6
            0 2 1 5 0 1
            3
            0 1 2
            4
            0 2 0 1
            6
            1 2 3 4 5 6
            """),
        ]
        expected = SequenceNode(items=[
            ItemNode(name='a'),
            NewlineNode(),
            LoopNode(size='a', name='i', body=SequenceNode(items=[
                ItemNode(name='b', indices=['i']),
                NewlineNode(),
                LoopNode(size='b_i', name='j', body=ItemNode(name='c', indices=['i', 'j'])),
                NewlineNode(),
            ])),
        ])

        actual = analyzer.construct_minimum_input_format_tree(instances=instances)
        self.assertEqual(str(actual), str(expected))

    def test_codeforces_1406_D(self) -> None:
        """It has many separated sample cases. Each case is complicated. Also they have zeros and negative values.
        """
        # https://codeforces.com/contest/1406/problem/D
        instances = [
            textwrap.dedent("""\
            4
            2 -1 7 3
            2
            2 4 -3
            3 4 2
            """),
            textwrap.dedent("""\
            6
            -9 -10 -9 -6 -5 4
            3
            2 6 -9
            1 2 -10
            4 6 -3
            """),
            textwrap.dedent("""\
            1
            0
            2
            1 1 -1
            1 1 -1
            """),
        ]
        expected = SequenceNode(items=[
            ItemNode(name='a'),
            NewlineNode(),
            LoopNode(size='a', name='i', body=ItemNode(name='b', indices=['i'])),
            NewlineNode(),
            ItemNode(name='c'),
            NewlineNode(),
            LoopNode(size='c', name='i', body=SequenceNode(items=[
                ItemNode(name='d', indices=['i']),
                ItemNode(name='e', indices=['i']),
                ItemNode(name='f', indices=['i']),
                NewlineNode(),
            ])),
        ])

        actual = analyzer.construct_minimum_input_format_tree(instances=instances)
        self.assertEqual(str(actual), str(expected))

    def test_atcoder_agc028_f(self) -> None:
        """It has many separated sample cases. Each case has non-integers which sometimes looks like integers.
        """
        # https://atcoder.jp/contests/agc028/tasks/agc028_f
        instances = [
            textwrap.dedent("""\
            2
            11
            11
            """),
            textwrap.dedent("""\
            4
            1111
            11#1
            1#11
            1111
            """),
            textwrap.dedent("""\
            10
            76##63##3#
            8445669721
            75#9542133
            3#285##445
            749632##89
            2458##9515
            5952578#77
            1#3#44196#
            4355#99#1#
            #298#63587
            """),
            textwrap.dedent("""\
            10
            4177143673
            7#########
            5#1716155#
            6#4#####5#
            2#3#597#6#
            6#9#8#3#5#
            5#2#899#9#
            1#6#####6#
            6#5359657#
            5#########
            """),
        ]
        expected = SequenceNode(items=[
            ItemNode(name='a'),
            NewlineNode(),
            LoopNode(size='a', name='i', body=SequenceNode(items=[
                ItemNode(name='b', indices=['i']),
                NewlineNode(),
            ])),
        ])

        actual = analyzer.construct_minimum_input_format_tree(instances=instances)
        self.assertEqual(str(actual), str(expected))
