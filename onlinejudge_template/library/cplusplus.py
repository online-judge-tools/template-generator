from typing import *

import onlinejudge_template.library.common as common
from onlinejudge_template.types import *


def _join_with_indent(lines: Sequence[str], *, nest: int, data: Dict[str, Any]) -> str:
    indent = data['config'].get('indent', ' ' * 4)
    buf = []
    nest = 1
    for line in lines:
        if line.startswith('}'):
            nest -= 1
        buf.append(indent * nest + line)
        if line.endswith('{'):
            nest += 1
    return '\n'.join(buf)


def _declare_loop(var: str, size: str, *, data: Dict[str, Any]) -> str:
    rep = data['config'].get('rep_macro')
    if rep is None:
        return f"""for (int {var} = 0; {var} < {size}; ++{var})"""
    elif isinstance(rep, str):
        return f"""{rep} ({var}, {size})"""
    elif callable(rep):
        return rep(var, size)
    else:
        assert False


def _read_int(var: str, *, data: Dict[str, Any]) -> str:
    scanner = data['config'].get('scanner')
    if scanner is None or scanner == 'scanf':
        return f"""scanf("%d", &{var});"""
    elif scanner in ('cin', 'std::cin'):
        return f"""{_get_std(data=data)}cin >> {var};"""
    elif callable(scanner):
        return scanner(var)
    else:
        assert False


def _write_int(var: str, *, data: Dict[str, Any]) -> str:
    printer = data['config'].get('printer')
    if printer is None or printer == 'scanf':
        return f"""printf("%d\\n", &{var});"""
    elif printer in ('cout', 'std::cout'):
        return f"""{_get_std(data=data)}cout << {var} << {_get_std(data=data)}endl;"""
    elif callable(printer):
        return printer(var)
    else:
        assert False


def _get_std(data: Dict['str', Any]) -> str:
    if data['config'].get('using_namespace_std', True):
        return ''
    else:
        return 'std::'


def _declare_variable(name: str, dims: List[str], *, data: Dict[str, Any]) -> str:
    type = "int"
    ctor = ""
    for dim in reversed(dims):
        ctor = f"""({dim}, {type}({ctor}))"""
        type = f"""{_get_std(data=data)}vector<{type} >"""
    return f"""{type} {name}{ctor};"""


def _read_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, List[str]], data: Dict[str, Any]) -> Iterator[str]:
    # declare all possible variables
    for var, decl in decls.items():
        if var not in declared and all([dep in initialized for dep in decl.depending]):
            yield _declare_variable(var, decl.dims, data=data)
            declared.add(var)

    # traverse AST
    if node.__class__.__name__ == 'ItemNode':
        if node.name not in declared:
            raise RuntimeError(f"""variable {node.name} is not declared yet""")
        var = node.name
        for index in node.indices:
            var = f"""{var}[{index}]"""
        yield f"""scanf("%d", &{var});"""
        initialized.add(node.name)
    elif node.__class__.__name__ == 'NewlineNode':
        pass
    elif node.__class__.__name__ == 'SequenceNode':
        for item in node.items:
            yield from _read_input_dfs(item, declared=declared, initialized=initialized, decls=decls, data=data)
    elif node.__class__.__name__ == 'LoopNode':
        yield _declare_loop(var=node.name, size=node.size, data=data) + ' {'
        declared.add(node.name)
        yield from _read_input_dfs(node.body, declared=declared, initialized=initialized, decls=decls, data=data)
        declared.remove(node.name)
        yield '}'


def read_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    decls = common.list_used_items(data['input'])
    lines = _read_input_dfs(data['input'], declared=set(), initialized=set(), decls=decls, data=data)
    return _join_with_indent(lines, nest=nest, data=data)


def write_output(data: Dict[str, Any], *, nest: int = 1) -> str:
    lines = []
    lines.append(_write_int('ans', data=data))
    return _join_with_indent(lines, nest=nest, data=data)


def arguments_types(data: Dict[str, Any]) -> str:
    decls = common.list_used_items(data['input'])
    args = []
    for name, decl in decls.items():
        type = "int"
        for _ in reversed(decl.dims):
            type = f"""{_get_std(data=data)}vector<{type} >"""
        if decl.dims:
            type = f"""const {type} &"""
        args.append(f"""{type} {name}""")
    return ', '.join(args)


def arguments(data: Dict[str, Any]) -> str:
    dims = common.list_used_items(data['input'])
    return ', '.join(dims.keys())


def return_type(data: Dict[str, Any]) -> str:
    return "auto"
