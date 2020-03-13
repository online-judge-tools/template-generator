import collections
import re
from typing import *

from onlinejudge_template.analyzer import simplify
from onlinejudge_template.types import *


class VarDecl(NamedTuple):
    name: str
    dims: List[str]
    bases: List[str]
    depending: Set[str]


class _CounterDecl(NamedTuple):
    name: str
    size: str
    depending: Set[str]


def _list_used_items_dfs(node: FormatNode, *, counter: Dict[str, _CounterDecl], declared: Dict[str, VarDecl]) -> None:
    if isinstance(node, ItemNode):
        if node.name in declared:
            raise NotImplementedError
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
            dims.append(str(simplify(f"""{dim} - ({base})""")))
            bases.append(str(simplify(base)))
        declared[node.name] = VarDecl(name=node.name, dims=dims, bases=bases, depending=depending)

    elif isinstance(node, NewlineNode):
        pass

    elif isinstance(node, SequenceNode):
        for item in node.items:
            _list_used_items_dfs(item, counter=counter, declared=declared)

    elif isinstance(node, LoopNode):
        depending = set()
        for n in declared.keys():
            if re.search(r'\b' + re.escape(n) + r'\b', node.size):
                depending.add(n)
        decl = _CounterDecl(name=node.name, size=node.size, depending=depending)
        _list_used_items_dfs(node.body, counter={node.name: decl, **counter}, declared=declared)


def list_used_items(node: FormatNode) -> Dict[str, VarDecl]:
    declared: Dict[str, VarDecl] = collections.OrderedDict()
    _list_used_items_dfs(node, counter={}, declared=declared)
    return declared


def get_indent(data: Dict['str', Any]) -> str:
    return data['config'].get('indent', ' ' * 4)
