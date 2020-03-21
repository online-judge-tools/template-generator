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

from onlinejudge_template.types import *
from onlinejudge_template.utils import simplify


class DeclaredVariablesError(AnalyzerError):
    pass


class _CounterDecl(NamedTuple):
    name: str
    size: str
    depending: Set[str]


def _list_declared_variables_dfs(node: FormatNode, *, counter: Dict[str, _CounterDecl], declared: Dict[str, VarDecl]) -> None:
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
                dim, _ = re.subn(r'\b' + re.escape(i) + r'\b', decl.size, dim)
                base, _ = re.subn(r'\b' + re.escape(i) + r'\b', '0', base)
            for n in declared.keys():
                if re.search(r'\b' + re.escape(n) + r'\b', dim):
                    depending.add(n)
            dims.append(simplify(f"""{dim} - ({base})""", env=set(declared.keys())))
            bases.append(simplify(base, env=set(declared.keys())))
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


def list_declared_variables(node: FormatNode) -> Dict[str, VarDecl]:
    """
    :raises DeclaredVariablesError:
    """

    declared: Dict[str, VarDecl] = collections.OrderedDict()
    _list_declared_variables_dfs(node, counter={}, declared=declared)
    return declared
