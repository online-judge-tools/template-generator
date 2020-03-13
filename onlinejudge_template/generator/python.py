from typing import *

import onlinejudge_template.generator.common as common
from onlinejudge_template.types import *

_DEDENT = '*DEDENT*'


def _join_with_indent(lines: Sequence[str], *, nest: int, data: Dict[str, Any]) -> str:
    indent = data['config'].get('indent', ' ' * 4)
    buf = []
    nest = 1
    for line in lines:
        if line == _DEDENT:
            nest -= 1
            continue
        buf.append(indent * nest + line)
        if line.endswith(':'):
            nest += 1
    return '\n'.join(buf)


def _get_variable(name: str, indices: List[str]) -> str:
    var = name
    for index in indices:
        var = f"""{var}[{index}]"""
    return var


def _declare_variable(name: str, dims: List[str], *, data: Dict[str, Any]) -> Iterator[str]:
    if dims:
        ctor = "None"
        for dim in reversed(dims):
            ctor = f"""[{ctor} for _ in range({dim})]"""
        yield f"""{name} = {ctor}"""


def _generate_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, List[str]], data: Dict[str, Any]) -> Iterator[str]:
    # declare all possible variables
    for var, decl in decls.items():
        if var not in declared and all([dep in initialized for dep in decl.depending]):
            yield from _declare_variable(var, decl.dims, data=data)
            declared.add(var)

    # traverse AST
    if node.__class__.__name__ == 'ItemNode':
        var = _get_variable(node.name, node.indices)
        yield f"""{var} = random.randint(1, 10 ** 9)  # TODO: edit here"""
        initialized.add(node.name)
    elif node.__class__.__name__ == 'NewlineNode':
        pass
    elif node.__class__.__name__ == 'SequenceNode':
        for item in node.items:
            yield from _generate_input_dfs(item, declared=declared, initialized=initialized, decls=decls, data=data)
    elif node.__class__.__name__ == 'LoopNode':
        yield f"""for {node.name} in range({node.size}):"""
        declared.add(node.name)
        yield from _generate_input_dfs(node.body, declared=declared, initialized=initialized, decls=decls, data=data)
        declared.remove(node.name)
        yield _DEDENT


def _write_input_dfs(node: FormatNode, *, data: Dict[str, Any]) -> Iterator[str]:
    if node.__class__.__name__ == 'ItemNode':
        var = _get_variable(node.name, node.indices)
        yield f"""print({var}, end=' ')"""
    elif node.__class__.__name__ == 'NewlineNode':
        yield "print()"
    elif node.__class__.__name__ == 'SequenceNode':
        for item in node.items:
            yield from _write_input_dfs(item, data=data)
    elif node.__class__.__name__ == 'LoopNode':
        yield f"""for {node.name} in range({node.size}):"""
        yield from _write_input_dfs(node.body, data=data)
        yield _DEDENT


def generate_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    decls = common.list_used_items(data['input'])
    lines = _generate_input_dfs(data['input'], declared=set(), initialized=set(), decls=decls, data=data)
    return _join_with_indent(lines, nest=nest, data=data)


def write_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    lines = _write_input_dfs(data['input'], data=data)
    return _join_with_indent(lines, nest=nest, data=data)
