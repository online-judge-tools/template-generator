"""
the module to analyze free variables in format trees

この module はフォーマット木の中に自由に出現する変数を分析します。
たとえば
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N",
            item("A", indices="i + 1")
        ),
        newline(),
    ])

のようなフォーマット木 (:any:`FormatNode`) が与えられれば
::

    {
        "N": {
        },
        "A": {
            "dims": ["N"],
            "bases": ["1"],
            "depending": ["N"],
        },
    }

のような情報 (:any:`VarDecl` を値とする辞書) を返します。
型の情報は取得できないことに注意してください。
"""

import collections
import re
from typing import *

from onlinejudge_template.analyzer.simplify import simplify
from onlinejudge_template.types import *


class DeclaredVariablesError(AnalyzerError):
    pass


class _CounterDecl(NamedTuple):
    name: VarName
    size: Expr
    depending: Set[VarName]


def _list_declared_variables_dfs(node: FormatNode, *, counter: Dict[VarName, _CounterDecl], declared: Dict[VarName, VarDecl]) -> None:
    """
    :raises DeclaredVariablesError:
    """

    if isinstance(node, ItemNode):
        if node.name in declared:
            raise DeclaredVariablesError(f"the same variable appears twice in tree: {node.name}")
        dims = []
        bases = []
        depending = set()
        for index in node.indices:
            dim = index
            base = index
            for i, decl in counter.items():
                dim = Expr(re.subn(r'\b' + re.escape(i) + r'\b', decl.size, dim)[0])
                base = Expr(re.subn(r'\b' + re.escape(i) + r'\b', '0', base)[0])
            for n in declared.keys():
                if re.search(r'\b' + re.escape(n) + r'\b', dim):
                    depending.add(n)
            dims.append(simplify(Expr(f"""{dim} - ({base})""")))
            bases.append(simplify(base))
        declared[node.name] = VarDecl(name=node.name, dims=dims, bases=bases, depending=depending, type=None)

    elif isinstance(node, NewlineNode):
        pass

    elif isinstance(node, SequenceNode):
        for item in node.items:
            _list_declared_variables_dfs(item, counter=counter, declared=declared)

    elif isinstance(node, LoopNode):
        depending = set()
        for n in declared.keys():
            if re.search(r'\b' + re.escape(n) + r'\b', node.size):
                depending.add(n)
        decl = _CounterDecl(name=node.name, size=node.size, depending=depending)
        _list_declared_variables_dfs(node.body, counter={node.name: decl, **counter}, declared=declared)


def list_declared_variables(node: FormatNode) -> Dict[VarName, VarDecl]:
    """
    :raises DeclaredVariablesError:
    """

    declared: Dict[VarName, VarDecl] = collections.OrderedDict()
    _list_declared_variables_dfs(node, counter={}, declared=declared)
    return declared
