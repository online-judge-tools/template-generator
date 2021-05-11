import textwrap
import unittest

import onlinejudge_template.analyzer.match as analyzer
from onlinejudge_template.types import *


class TestMinimumTree(unittest.TestCase):
    def test_simple(self) -> None:
        node = SequenceNode(items=[
            ItemNode(indices=[], name='testcases'),
            NewlineNode(),
            LoopNode(name='i', size='testcases', body=SequenceNode(items=[
                ItemNode(indices=['i'], name='a'),
                NewlineNode(),
                LoopNode(body=ItemNode(indices=['i', 'j'], name='b'), name='j', size='a_i'),
                NewlineNode(),
            ])),
        ])
        data = textwrap.dedent("""\
        3
        5
        5 3 2 1 4
        6
        2 2 2 2 2 2
        2
        2 1
        """)
        variables = [
            VarDecl(name=VarName('testcases'), type=None, dims=[], bases=[], depending=set()),
            VarDecl(name=VarName('a'), type=None, dims=[Expr('testcases')], bases=[Expr('0')], depending={VarName('testcases')}),
            VarDecl(name=VarName('b'), type=None, dims=[Expr('testcases'), Expr('a_i')], bases=[Expr('0'), Expr('0')], depending={VarName('testcases')}),
        ]

        expected: Dict[str, Any] = {
            'testcases': {
                (): 3
            },
            'a': {(i, ): a_i
                  for (i, a_i) in enumerate([5, 6, 2])},
            'b': {(i, j): b_i_j
                  for i, b_i in enumerate([[5, 3, 2, 1, 4], [2, 2, 2, 2, 2, 2], [2, 1]]) for j, b_i_j in enumerate(b_i)},
        }

        actual = analyzer.match_format(node=node, data=data, variables={decl.name: decl for decl in variables})
        self.assertEqual(actual, expected)
