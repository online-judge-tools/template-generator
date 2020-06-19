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
import itertools
import re
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
    """_make_tree_patterns detects patterns which have the variable `n` and arrays with lentgh `n`, and replaces the length of arrays with `n - 1`.
    """

    tree_patterns = []
    for pattern in patterns:
        pattern, replaced = _make_tree_pattern_dfs(pattern)
        if replaced:
            tree_patterns.append(pattern)
    return tree_patterns


@functools.lru_cache(maxsize=None)
def list_all_patterns() -> List[Tuple[FormatNode, Dict[str, VarDecl]]]:
    """list_all_patterns lists all pre-defined petterns.
    """

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


def list_output_patterns_depending_input_variable(n: str) -> List[FormatNode]:
    """list_output_patterns_depending_input_variable lists output patterns which depend input patterns.

    :param n: is the name of the variable which represents the length of array.
    """

    assert n not in ('ans', 'i')
    vector_pattern = SequenceNode(items=[
        LoopNode(name='i', size=n, body=ItemNode(name='ans', indices=['i'])),
        NewlineNode(),
    ])
    vertical_vector_pattern = LoopNode(name='i', size=n, body=SequenceNode(items=[
        ItemNode(name='ans', indices=['i']),
        NewlineNode(),
    ]))
    all_patterns = [vector_pattern, vertical_vector_pattern]
    return all_patterns


def _rename_variables_if_conflicts_dfs(node: FormatNode, *, mapping: Dict[str, str], env: Dict[str, VarDecl]) -> FormatNode:
    def rename(s: str) -> str:
        for a, b in mapping.items():
            s = re.sub(r'\b' + re.escape(a) + r'\b', b, s)
        return s

    if isinstance(node, ItemNode):
        assert node.name not in mapping  # because there are only such patterns
        if node.name not in env:
            return node
        else:
            for i in itertools.count(1):
                new_name = node.name + str(i)
                if new_name not in env:
                    mapping[node.name] = new_name
                    break
            indices = list(map(rename, node.indices))
            return ItemNode(name=mapping[node.name], indices=indices)

    elif isinstance(node, NewlineNode):
        return node

    elif isinstance(node, SequenceNode):
        items: List[FormatNode] = []
        for item in node.items:
            items.append(_rename_variables_if_conflicts_dfs(item, mapping=mapping, env=env))
        return SequenceNode(items=items)

    elif isinstance(node, LoopNode):
        body = _rename_variables_if_conflicts_dfs(node.body, mapping=mapping, env=env)
        return LoopNode(name=node.name, size=rename(node.size), body=body)

    else:
        assert False


def rename_variables_if_conflicts(node: FormatNode, *, env: Dict[str, VarDecl]) -> FormatNode:
    return _rename_variables_if_conflicts_dfs(node, mapping={}, env=env)


def guess_format_with_pattern_matching(*, instances: List[bytes]) -> Optional[FormatNode]:
    """guess_format_with_pattern_matching guesses a format tree from the strings which match with the format tree, i.e. sample cases.

    :param instances: are sample cases.
    """

    found: List[FormatNode] = []

    # patterns without variables in the input format
    for pattern, variables in list_all_patterns():
        pattern = rename_variables_if_conflicts(pattern, env={})
        try:
            for data in instances:
                match_format(pattern, data.decode(), variables=variables)
        except FormatMatchError:
            pass
        else:
            logger.debug('simple pattern found: %s', pattern)
            found.append(pattern)

    if len(found) == 1:
        return found[0]
    else:
        return None


def guess_output_format_with_pattern_matching_using_input_format(*, instances: List[SampleCase], input_format: FormatNode, input_variables: Dict[str, VarDecl]) -> Optional[FormatNode]:
    """guess_output_format_with_pattern_matching_using_input_format

    :param instances: are sample cases.
    :param input_format:
    :param input_variables:
    """

    found: List[FormatNode] = []

    # patterns without variables in the input format
    for pattern, variables in list_all_patterns():
        try:
            for data in instances:
                match_format(pattern, data.output.decode(), variables=variables)
        except FormatMatchError:
            pass
        else:
            pattern = rename_variables_if_conflicts(pattern, env=input_variables)
            logger.debug('simple output pattern found without input variables: %s', pattern)
            found.append(pattern)

    # patterns with variables in the input format
    for name in ('n', 'N', 'm', 'M', 't', 'T'):
        if name in input_variables and input_variables[name].type in (VarType.IndexInt, VarType.ValueInt):
            env = dict(input_variables)
            env.pop(name)
            for pattern in list_output_patterns_depending_input_variable(name):

                # prepare pattern
                pattern = rename_variables_if_conflicts(pattern, env=env)
                try:
                    variables = onlinejudge_template.analyzer.variables.list_declared_variables(pattern)
                except onlinejudge_template.analyzer.variables.DeclaredVariablesError:
                    assert False
                assert name not in variables

                # try matching
                try:
                    for data in instances:
                        input_values = match_format(input_format, data.input.decode(), variables=input_variables)
                        values = {name: input_values[name]}  # hide variables other than the `name`
                        match_format(pattern, data.output.decode(), variables=variables, values=values)
                except FormatMatchError as e:
                    logger.exception(e)
                    pass
                else:
                    logger.debug('simple output pattern found with input variables: %s', pattern)
                    found.append(pattern)

    if len(found) == 1:
        return found[0]
    else:
        return None
