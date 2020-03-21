"""
the module to guess format trees from sample strings

この module はサンプル文字列から直接 (つまり、フォーマット文字列を用いずに) フォーマット木を推測します。
単純なフォーマット木を列挙しておき、それらとのパターンマッチをすることによって実装されています。

たとえば
::

    6
    1 3 8 7 10 2

というサンプル文字列から
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N",
            item("A", indices="i")
        ),
        newline(),
    ])

のようなフォーマット木 (:any:`FormatNode`) を作ります。
"""

import functools
import random
import re
import string
from logging import getLogger
from typing import *

import onlinejudge_template.analyzer.variables
from onlinejudge_template.analyzer.match import FormatMatchError, match_format
from onlinejudge_template.types import *

logger = getLogger(__name__)


class SimplePatternMatchingError(AnalyzerError):
    pass


# simple patterns
_one_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    NewlineNode(),
])

_two_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    ItemNode(name='b', indices=[]),
    NewlineNode(),
])

_three_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    ItemNode(name='b', indices=[]),
    ItemNode(name='c', indices=[]),
    NewlineNode(),
])

_four_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    ItemNode(name='b', indices=[]),
    ItemNode(name='c', indices=[]),
    ItemNode(name='d', indices=[]),
    NewlineNode(),
])

_simple_patterns = [
    _one_pattern,
    _two_pattern,
    _three_pattern,
    _four_pattern,
]

# simple patterns (vertical versions)
_vertical_two_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    NewlineNode(),
    ItemNode(name='b', indices=[]),
    NewlineNode(),
])

_vertical_three_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    NewlineNode(),
    ItemNode(name='b', indices=[]),
    NewlineNode(),
    ItemNode(name='c', indices=[]),
    NewlineNode(),
])

_vertical_four_pattern = SequenceNode(items=[
    ItemNode(name='a', indices=[]),
    NewlineNode(),
    ItemNode(name='b', indices=[]),
    NewlineNode(),
    ItemNode(name='c', indices=[]),
    NewlineNode(),
    ItemNode(name='d', indices=[]),
    NewlineNode(),
])

_vertical_simple_patterns = [
    _two_pattern,
    _three_pattern,
    _four_pattern,
]

# one vector patterns
_length_and_vector_pattern = SequenceNode(items=[
    ItemNode(name='n', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=ItemNode(name='a', indices=['i'])),
    NewlineNode(),
])

_length_and_vertical_vector_pattern = SequenceNode(items=[
    ItemNode(name='n', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=SequenceNode(items=[
        ItemNode(name='a', indices=['i']),
        NewlineNode(),
    ])),
])

_one_vector_patterns = [
    _length_and_vector_pattern,
    _length_and_vertical_vector_pattern,
]

# one vector patterns (with data)
_length_data_and_vector_pattern = SequenceNode(items=[
    ItemNode(name='n', indices=[]),
    ItemNode(name='k', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=ItemNode(name='a', indices=['i'])),
    NewlineNode(),
])

_data_length_and_vector_pattern = SequenceNode(items=[
    ItemNode(name='k', indices=[]),
    ItemNode(name='n', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=ItemNode(name='a', indices=['i'])),
    NewlineNode(),
])

_length_data_and_vertical_vector_pattern = SequenceNode(items=[
    ItemNode(name='n', indices=[]),
    ItemNode(name='k', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=SequenceNode(items=[
        ItemNode(name='a', indices=['i']),
        NewlineNode(),
    ])),
])

_data_length_and_vertical_vector_pattern = SequenceNode(items=[
    ItemNode(name='k', indices=[]),
    ItemNode(name='n', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=SequenceNode(items=[
        ItemNode(name='a', indices=['i']),
        NewlineNode(),
    ])),
])

_one_vector_with_data_patterns = [
    _length_data_and_vector_pattern,
    _data_length_and_vector_pattern,
    _length_data_and_vertical_vector_pattern,
    _data_length_and_vertical_vector_pattern,
]

# two vectors patterns
_length_and_two_vector_pattern = SequenceNode(items=[
    ItemNode(name='n', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=ItemNode(name='a', indices=['i'])),
    NewlineNode(),
    LoopNode(name='i', size='n', body=ItemNode(name='b', indices=['i'])),
    NewlineNode(),
])

_length_and_vertical_two_vector_pattern = SequenceNode(items=[
    ItemNode(name='n', indices=[]),
    NewlineNode(),
    LoopNode(name='i', size='n', body=SequenceNode(items=[
        ItemNode(name='a', indices=['i']),
        ItemNode(name='b', indices=['i']),
        NewlineNode(),
    ])),
])

_two_vectors_patterns = [
    _length_and_two_vector_pattern,
    _length_and_vertical_two_vector_pattern,
]


def _make_tree_pattern_dfs(node: FormatNode) -> Tuple[FormatNode, bool]:
    if isinstance(node, ItemNode):
        return node, False

    elif isinstance(node, NewlineNode):
        return node, False

    elif isinstance(node, SequenceNode):
        items: List[FormatNode] = []
        any_replaced = False
        for item in node.items:
            item, replaced = _make_tree_pattern_dfs(item)
            if replaced:
                any_replaced = True
        return SequenceNode(items=items), any_replaced

    elif isinstance(node, LoopNode):
        assert node.size == 'n'
        body, _ = _make_tree_pattern_dfs(node.body)
        return LoopNode(name=node.name, size='n - 1', body=body), True

    else:
        assert False


def _make_tree_patterns(patterns: List[FormatNode]) -> List[FormatNode]:
    tree_patterns = []
    for pattern in patterns:
        pattern, replaced = _make_tree_pattern_dfs(pattern)
        if replaced:
            tree_patterns.append(pattern)
    return tree_patterns


@functools.lru_cache(maxsize=None)
def list_all_patterns() -> List[Tuple[FormatNode, Dict[str, VarDecl]]]:
    patterns: List[FormatNode] = [
        *_simple_patterns,
        *_vertical_simple_patterns,
        *_one_vector_patterns,
        *_one_vector_with_data_patterns,
        *_two_vectors_patterns,
    ]
    all_patterns = patterns + _make_tree_patterns(patterns)

    results: List[Tuple[FormatNode, Dict[str, VarDecl]]] = []
    for pattern in all_patterns:
        try:
            variables = onlinejudge_template.analyzer.variables.list_declared_variables(pattern)
            results.append((pattern, variables))
        except onlinejudge_template.analyzer.variables.DeclaredVariablesError:
            assert False
    return results


def _randomize_variables_dfs(node: FormatNode, *, mapping: Dict[str, str]) -> FormatNode:
    def rename(s: str) -> str:
        for a, b in mapping.items():
            s = re.sub(r'\b' + re.escape(a) + r'\b', b, s)
        return s

    if isinstance(node, ItemNode):
        assert node.name not in mapping
        mapping[node.name] = random.choice(string.ascii_lowercase) + random.choice(string.ascii_lowercase) + random.choice(string.ascii_lowercase)
        indices = list(map(rename, node.indices))
        return ItemNode(name=mapping[node.name], indices=indices)

    elif isinstance(node, NewlineNode):
        return node

    elif isinstance(node, SequenceNode):
        items: List[FormatNode] = []
        for item in node.items:
            items.append(_randomize_variables_dfs(item, mapping=mapping))
        return SequenceNode(items=items)

    elif isinstance(node, LoopNode):
        body = _randomize_variables_dfs(node.body, mapping=mapping)
        return LoopNode(name=node.name, size=rename(node.size), body=body)

    else:
        assert False


def randomize_variables(node: FormatNode) -> FormatNode:
    return _randomize_variables_dfs(node, mapping={})


def guess_format_with_pattern_matching(*, instances: List[bytes]) -> Optional[FormatNode]:
    found: List[FormatNode] = []
    for pattern, variables in list_all_patterns():
        try:
            for data in instances:
                match_format(pattern, data.decode(), variables=variables)
            found.append(pattern)
        except FormatMatchError:
            pass
    if len(found) == 1:
        return randomize_variables(found[0])
    else:
        return None
