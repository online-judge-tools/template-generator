import string
from typing import *

import onlinejudge_template.analyzer.simplify as simplify
from onlinejudge_template.types import *


def remove_superfluous_sequence_nodes(node: FormatNode) -> FormatNode:
    if isinstance(node, ItemNode):
        return node
    elif isinstance(node, NewlineNode):
        return node
    elif isinstance(node, SequenceNode):
        items = []
        for item in node.items:
            item = remove_superfluous_sequence_nodes(item)
            if isinstance(item, SequenceNode):
                items.extend(item.items)
            else:
                items.append(item)
        if len(items) == 1:
            return items[0]
        return SequenceNode(items=items)
    elif isinstance(node, LoopNode):
        return LoopNode(size=node.size, name=node.name, body=remove_superfluous_sequence_nodes(node.body))
    else:
        assert False


def _get_nice_variable_name(*, used: Set[VarName]) -> VarName:
    for c in map(VarName, 'abcdefgh' + 'mnopqrstuvwxyz'):
        if c not in used:
            return c
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            for c3 in string.ascii_uppercase:
                s = VarName('a' + c1 + c2 + c3)
                if s not in used:
                    return s
    assert False


def _get_nice_counter_name(*, used: Set[VarName]) -> VarName:
    for c in map(VarName, 'ijkl'):
        if c not in used:
            return c
    for c1 in string.ascii_uppercase:
        for c2 in string.ascii_uppercase:
            for c3 in string.ascii_uppercase:
                s = VarName('i' + c1 + c2 + c3)
                if s not in used:
                    return s
    assert False


def _rename_variable_nicely_dfs(node: FormatNode, *, replace: Dict[VarName, VarName], used: Set[VarName]) -> FormatNode:
    if isinstance(node, ItemNode):
        name = _get_nice_variable_name(used=used)
        indices = [simplify.rename_variables_in_expr(index, replace=replace) for index in node.indices]

        assert node.name not in replace
        replace[node.name] = name
        used.add(name)
        return ItemNode(name=name, indices=indices)

    elif isinstance(node, NewlineNode):
        return NewlineNode()

    elif isinstance(node, SequenceNode):
        items = []
        for item in node.items:
            items.append(_rename_variable_nicely_dfs(item, replace=replace, used=used))
        return SequenceNode(items=items)

    elif isinstance(node, LoopNode):
        name = _get_nice_counter_name(used=used)
        size = simplify.rename_variables_in_expr(node.size, replace=replace)

        assert node.name not in replace
        replace[node.name] = name
        used.add(name)
        body = _rename_variable_nicely_dfs(node.body, replace=replace, used=used)
        used.remove(name)
        replace.pop(node.name)
        return LoopNode(size=size, name=name, body=body)

    else:
        assert False


def rename_variable_nicely(node: FormatNode, *, used: Optional[Set[VarName]] = None) -> FormatNode:
    return _rename_variable_nicely_dfs(node, replace={}, used=used or set())
