import collections
import re
from typing import *

from onlinejudge_template.analyzer import simplify
from onlinejudge_template.types import *


def _list_used_items_dfs(node: FormatNode, *, counter: Dict[str, str], declared: Dict[str, List[str]]) -> None:
    if node.__class__.__name__ == 'ItemNode':
        if node.name in declared:
            raise NotImplementedError
        dims = []
        for index in node.indices:
            for i, size in counter.items():
                index, _ = re.subn(r'\b' + re.escape(i) + r'\b', size, index)
            dims.append(str(simplify(index)))
        declared[node.name] = dims

    elif node.__class__.__name__ == 'NewlineNode':
        pass

    elif node.__class__.__name__ == 'SequenceNode':
        for item in node.items:
            _list_used_items_dfs(item, counter=counter, declared=declared)

    elif node.__class__.__name__ == 'LoopNode':
        _list_used_items_dfs(node.body, counter={node.name: node.size, **counter}, declared=declared)


def list_used_items(node: FormatNode) -> Dict[str, List[str]]:
    declared: Dict[str, List[str]] = collections.OrderedDict()
    _list_used_items_dfs(node, counter={}, declared=declared)
    return declared


def get_indent(indent: Optional[str], *, data: Dict['str', Any]) -> str:
    if indent is not None:
        return indent
    else:
        return data['config'].get('indent', ' ' * 4)
