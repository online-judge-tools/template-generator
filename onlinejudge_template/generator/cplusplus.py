import abc
from typing import *

import onlinejudge_template.generator.common as common
from onlinejudge_template.analyzer import simplify
from onlinejudge_template.types import *


class CPlusPlusNode(abc.ABC):
    def __repr__(self) -> str:
        keys = dir(self)
        keys = list(filter(lambda key: not key.startswith('_'), keys))
        keys.sort()
        items = ', '.join([key + '=' + repr(getattr(self, key)) for key in keys])
        return f"{self.__class__.__name__}({items})"


class DeclNode(CPlusPlusNode):
    def __init__(self, decls: List[common.VarDecl]):
        self.decls = decls


class InputNode(CPlusPlusNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class OutputTokensNode(CPlusPlusNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class OutputNewlineNode(CPlusPlusNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class SentencesNode(CPlusPlusNode):
    def __init__(self, sentences: List[CPlusPlusNode]):
        self.sentences = sentences


class RepeatNode(CPlusPlusNode):
    def __init__(self, name: str, size: str, body: CPlusPlusNode):
        self.name = name
        self.size = size
        self.body = body


class OtherNode(CPlusPlusNode):
    def __init__(self, line: str):
        self.line = line


def _join_with_indent(lines: Iterator[str], *, nest: int, data: Dict[str, Any]) -> str:
    indent = common.get_indent(data=data)
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


def _read_ints(exprs: List[str], *, data: Dict[str, Any]) -> List[str]:
    if not exprs:
        return []
    scanner = data['config'].get('scanner')
    if scanner is None or scanner == 'scanf':
        return [f"""scanf("{'%d' * len(exprs)}", &{', &'.join(exprs)});"""]
    elif scanner in ('cin', 'std::cin'):
        return [f"""{_get_std(data=data)}cin >> {' >> '.join(exprs)};"""]
    elif callable(scanner):
        return scanner(exprs)
    else:
        assert False


def _write_ints(exprs: List[str], *, newline: bool, data: Dict[str, Any]) -> List[str]:
    printer = data['config'].get('printer')
    if printer is None or printer == 'printf':
        return [f"""printf("{' '.join(['%d'] * len(exprs))}\\n", {', '.join(exprs)});"""]
    elif printer in ('cout', 'std::cout'):
        return [f"""{_get_std(data=data)}cout << {" << ' ' << ".join(exprs)} << {_get_std(data=data)}endl;"""]
    elif callable(printer):
        return printer(exprs, newline=newline)
    else:
        assert False


def _get_std(data: Dict['str', Any]) -> str:
    if data['config'].get('using_namespace_std', True):
        return ''
    else:
        return 'std::'


def _get_type_and_ctor(decl: common.VarDecl, *, data: Dict[str, Any]) -> Tuple[str, str]:
    type = "int"
    ctor = ""
    for dim in reversed(decl.dims):
        sndarg = f""", {type}({ctor})""" if ctor else ''
        ctor = f"""({dim}{sndarg})"""
        space = ' ' if type.endswith('>') else ''
        type = f"""{_get_std(data=data)}vector<{type}{space}>"""
    return type, ctor


def _get_variable(*, decl: common.VarDecl, indices: List[str]) -> str:
    var = decl.name
    for index, base in zip(indices, decl.bases):
        i = str(simplify(f"""{index} - ({base})"""))
        var = f"""{var}[{i}]"""
    return var


def _declare_variables(decls: List[common.VarDecl], *, data: Dict[str, Any]) -> Iterator[str]:
    last_type = None
    last_inits = []
    for decl in decls:
        type, ctor = _get_type_and_ctor(decl, data=data)
        if last_type != type and last_type is not None:
            yield f"""{type} {", ".join(last_inits)};"""
            last_inits = []
        last_type = type
        last_inits.append(f"""{decl.name}{ctor}""")
    if last_type is not None:
        yield f"""{type} {", ".join(last_inits)};"""


def _read_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, common.VarDecl], data: Dict[str, Any]) -> CPlusPlusNode:
    # declare all possible variables
    new_decls: List[CPlusPlusNode] = []
    for var, decl in decls.items():
        if var not in declared and all([dep in initialized for dep in decl.depending]):
            new_decls.append(DeclNode(decls=[decl]))
            declared.add(var)
    if new_decls:
        return SentencesNode(sentences=new_decls + [_read_input_dfs(node, declared=declared, initialized=initialized, decls=decls, data=data)])

    # traverse AST
    if isinstance(node, ItemNode):
        if node.name not in declared:
            raise RuntimeError(f"""variable {node.name} is not declared yet""")
        initialized.add(node.name)
        var = _get_variable(decl=decls[node.name], indices=node.indices)
        return InputNode(exprs=[var])
    elif isinstance(node, NewlineNode):
        return SentencesNode(sentences=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_read_input_dfs(item, declared=declared, initialized=initialized, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        declared.add(node.name)
        body = _read_input_dfs(node.body, declared=declared, initialized=initialized, decls=decls, data=data)
        result = RepeatNode(name=node.name, size=node.size, body=body)
        declared.remove(node.name)
        return result
    else:
        assert False


def _write_output_dfs(node: FormatNode, *, decls: Dict[str, common.VarDecl], data: Dict[str, Any]) -> CPlusPlusNode:
    if isinstance(node, ItemNode):
        var = _get_variable(decl=decls[node.name], indices=node.indices)
        return OutputTokensNode(exprs=[var])
    elif isinstance(node, NewlineNode):
        return OutputNewlineNode(exprs=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_write_output_dfs(item, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        body = _write_output_dfs(node.body, decls=decls, data=data)
        result = RepeatNode(name=node.name, size=node.size, body=body)
        return result
    else:
        assert False


def _optimize_syntax_tree(node: CPlusPlusNode, *, data: Dict[str, Any]) -> CPlusPlusNode:
    if isinstance(node, DeclNode):
        return node
    elif isinstance(node, InputNode):
        return node
    elif isinstance(node, OutputTokensNode):
        return node
    elif isinstance(node, OutputNewlineNode):
        return node
    elif isinstance(node, SentencesNode):
        sentences: List[CPlusPlusNode] = []
        que = [_optimize_syntax_tree(sentence, data=data) for sentence in node.sentences]
        while que:
            sentence, *que = que
            if sentences and isinstance(sentences[-1], DeclNode) and isinstance(sentence, DeclNode):
                sentences[-1].decls.extend(sentence.decls)
            elif sentences and isinstance(sentences[-1], InputNode) and isinstance(sentence, InputNode):
                sentences[-1].exprs.extend(sentence.exprs)
            elif sentences and isinstance(sentences[-1], OutputTokensNode) and isinstance(sentence, OutputTokensNode):
                sentences[-1].exprs.extend(sentence.exprs)
            elif sentences and isinstance(sentences[-1], OutputTokensNode) and isinstance(sentence, OutputNewlineNode):
                sentences[-1] = OutputNewlineNode(exprs=sentences[-1].exprs + sentence.exprs)
            elif isinstance(sentence, SentencesNode):
                que = sentence.sentences + que
            else:
                sentences.append(sentence)
        return SentencesNode(sentences=sentences)
    elif isinstance(node, RepeatNode):
        return RepeatNode(name=node.name, size=node.size, body=_optimize_syntax_tree(node.body, data=data))
    elif isinstance(node, OtherNode):
        return node
    else:
        assert False


def _serialize_syntax_tree(node: CPlusPlusNode, *, data: Dict[str, Any]) -> Iterator[str]:
    if isinstance(node, DeclNode):
        yield from _declare_variables(node.decls, data=data)
    elif isinstance(node, InputNode):
        yield from _read_ints(node.exprs, data=data)
    elif isinstance(node, OutputTokensNode):
        yield from _write_ints(node.exprs, newline=False, data=data)
    elif isinstance(node, OutputNewlineNode):
        yield from _write_ints(node.exprs, newline=True, data=data)
    elif isinstance(node, SentencesNode):
        for sentence in node.sentences:
            yield from _serialize_syntax_tree(sentence, data=data)
    elif isinstance(node, RepeatNode):
        yield _declare_loop(var=node.name, size=node.size, data=data) + ' {'
        yield from _serialize_syntax_tree(node.body, data=data)
        yield '}'
    elif isinstance(node, OtherNode):
        yield node.line
    else:
        assert False


def read_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    if data['input'] is None:
        lines = [
            '// failed to analyze input format',
            'int n;  // TODO: edit here',
            *_read_ints(['n'], data=data),
            f"""{_get_std(data=data)}vector<int> a(n);""",
            _declare_loop('i', 'n', data=data) + ' {',
            *_read_ints(['a[i]'], data=data),
            '}',
        ]
        return _join_with_indent(iter(lines), nest=nest, data=data)

    decls = common.list_used_items(data['input'])
    node = _read_input_dfs(data['input'], declared=set(), initialized=set(), decls=decls, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def write_output(data: Dict[str, Any], *, nest: int = 1) -> str:
    if data['output'] is None:
        lines = [
            '// failed to analyze output format',
            *_write_ints(['ans'], newline=True, data=data),
        ]
        lines[0] += "  // TODO: edit here"
        return _join_with_indent(iter(lines), nest=nest, data=data)

    decls = common.list_used_items(data['output'])
    node = _write_output_dfs(data['output'], decls=decls, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def arguments_types(data: Dict[str, Any]) -> str:
    if data['input'] is None:
        return f"""int n, const {_get_std(data=data)}<int> & a"""

    decls = common.list_used_items(data['input'])
    args = []
    for name, decl in decls.items():
        type = "int"
        for _ in reversed(decl.dims):
            space = ' ' if type.endswith('>') else ''
            type = f"""{_get_std(data=data)}vector<{type}{space}>"""
        if decl.dims:
            type = f"""const {type} &"""
        args.append(f"""{type} {name}""")
    return ', '.join(args)


def arguments(data: Dict[str, Any]) -> str:
    if data['input'] is None:
        return 'n, a'

    decls = common.list_used_items(data['input'])
    return ', '.join(decls.keys())


def return_type(data: Dict[str, Any]) -> str:
    return "auto"


def return_values(data: Dict[str, Any]) -> str:
    if data['output'] is None:
        return 'ans'

    decls = common.list_used_items(data['output'])
    keys = list(decls.keys())
    if len(keys) == 1:
        return keys[0]
    else:
        return f"""[{', '.join(decls.keys())}]"""
