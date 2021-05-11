"""
the module to generate C++ code

この module は C++ のコードを生成します。

以下の関数を提供します。

- :func:`read_input`
- :func:`write_output`
- :func:`declare_constants`
- :func:`formal_arguments`
- :func:`actual_arguments`
- :func:`return_type`
- :func:`return_value`

次のように利用することが想定されています。

.. code-block:: c++

    #include ...
    ...

    ${cplusplus.declare_constants(data)}
    ${cplusplus.return_type(data)} solve(${cplusplus.formal_arguments(data)}) {
        ...
    }

    int main() {
    ${cplusplus.read_input(data)}
        auto ${cplusplus.return_value(data)} = solve(${cplusplus.actual_arguments(data)});
    ${cplusplus.write_output(data)}
    }

加えて、ランダムケースの生成のために、以下の関数を提供します。

- :func:`generate_input`
- :func:`write_input`
"""

from logging import getLogger
from typing import *

import onlinejudge_template.generator._utils as utils
from onlinejudge_template.analyzer.simplify import simplify
from onlinejudge_template.generator._cplusplus import *
from onlinejudge_template.types import *

logger = getLogger(__name__)


def _join_with_indent(lines: Iterator[str], *, nest: int, data: Dict[str, Any]) -> str:
    indent = utils.get_indent(data=data)
    buf = []
    for line in lines:
        if line.startswith('}'):
            nest -= 1
        buf.append(indent * nest + line)
        if line.endswith('{'):
            nest += 1
    return '\n'.join(buf)


def _declare_loop(var: VarName, size: str, *, data: Dict[str, Any]) -> str:
    """
    :raises CPlusPlusGeneratorError:
    """

    rep = data['config'].get('rep_macro')
    if rep is None:
        return f"""for (int {var} = 0; {var} < {size}; ++{var})"""
    elif isinstance(rep, str):
        return f"""{rep} ({var}, {size})"""
    elif callable(rep):
        return rep(var, size)
    else:
        raise CPlusPlusGeneratorError(f"""invalid "rep_macro" config: {rep}""")


def _read_variables(exprs: List[Tuple[str, Optional[VarType]]], *, data: Dict[str, Any]) -> List[str]:
    """
    :raises CPlusPlusGeneratorError:
    """

    if not exprs:
        return []
    scanner = data['config'].get('scanner')
    if scanner == 'scanf':
        specifiers = ''
        arguments = ['']
        for expr, type in exprs:
            specifiers += _get_base_type_format_specifier(type, name=expr, data=data)
            arguments.append('&' + expr)
        return [f"""scanf("{specifiers}"{', '.join(arguments)});"""]
    elif scanner is None or scanner in ('cin', 'std::cin'):
        items = []
        items.append(f"""std::cin""")
        for expr, _ in exprs:
            items.append(expr)
        return [" >> ".join(items) + ";"]
    elif callable(scanner):
        return scanner(exprs)
    else:
        raise CPlusPlusGeneratorError(f"""invalid "scanner" config: {scanner}""")


def _write_variables(exprs: List[Tuple[str, Optional[VarType]]], *, end: str, data: Dict[str, Any]) -> List[str]:
    """
    :raises CPlusPlusGeneratorError:
    """

    assert end in ('', ' ', '\n')
    printer = data['config'].get('printer')
    if printer == 'printf':
        specifiers = ''
        arguments = ['']
        for expr, type in exprs:
            specifiers += _get_base_type_format_specifier(type, name=expr, data=data)
            arguments.append(expr)
        if end == '\n':
            end = '\\n'
        return [f"""printf("{specifiers}{end}"{', '.join(arguments)});"""]
    elif printer is None or printer in ('cout', 'std::cout'):
        items = []
        items.append(f"""std::cout""")
        for i, (expr, _) in enumerate(exprs):
            if i:
                items.append("""' '""")
            items.append(expr)
        if end == ' ':
            items.append("' '")
        elif end == '\n':
            items.append("'\\n'")
        return [" << ".join(items) + ";"]
    elif callable(printer):
        return printer(exprs, newline=(end == '\n'))
    else:
        raise CPlusPlusGeneratorError(f"""invalid "printer" config: {printer}""")


def _generate_variable(expr: Tuple[str, Optional[VarType]], *, data: Dict[str, Any]) -> Iterator[str]:
    """
    :raises CPlusPlusGeneratorError:
    """

    name, type = expr
    if type is None:
        type = VarType.IndexInt
    if type == VarType.IndexInt:
        l, r = 0, 10**5 + 1
    elif type == VarType.ValueInt:
        l, r = 0, 10**9 + 1
    else:
        raise CPlusPlusGeneratorError(f"""cannot generate a variable of type {type}: {repr(name)}""")

    yield f"""{name} = std::uniform_int_distribution<{_get_base_type(type, data=data)}>({l}, {r - 1})(gen);"""


def _get_base_type(type: Optional[VarType], *, data: Dict[str, Any]) -> str:
    if type == VarType.IndexInt:
        return "int"
    elif type == VarType.ValueInt:
        return data['config'].get('long_long_int', "long long")
    elif type == VarType.Float:
        return "double"
    elif type == VarType.String:
        return f"""std::string"""
    elif type == VarType.Char:
        return "char"
    elif type is None:
        return "auto"
    else:
        assert False


def _get_base_type_format_specifier(type: Optional[VarType], *, name: str, data: Dict[str, Any]) -> str:
    """
    :raises CPlusPlusGeneratorError:
    """

    if type == VarType.IndexInt:
        return "%d"
    elif type == VarType.ValueInt:
        return "%lld"
    elif type == VarType.Float:
        return "%lf"
    elif type == VarType.String:
        raise CPlusPlusGeneratorError(f"""scanf()/printf() cannot read/write std::string variables: {name}""")
    elif type == VarType.Char:
        return " %c"
    elif type is None:
        raise CPlusPlusGeneratorError(f"""type is unknown: {name}""")
    else:
        assert False


def _get_type_and_ctor(decl: VarDecl, *, data: Dict[str, Any]) -> Tuple[str, str]:
    type = _get_base_type(decl.type, data=data)
    ctor = ""
    for dim in reversed(decl.dims):
        sndarg = f""", {type}({ctor})""" if ctor else ''
        ctor = f"""({dim}{sndarg})"""
        space = ' ' if type.endswith('>') else ''
        type = f"""std::vector<{type}{space}>"""
    return type, ctor


def _get_variable(*, decl: VarDecl, indices: List[Expr], decls: Dict[VarName, VarDecl]) -> str:
    var = str(decl.name)
    for index, base in zip(indices, decl.bases):
        i = simplify(Expr(f"""{index} - ({base})"""))
        var = f"""{var}[{i}]"""
    return var


def _declare_variables(decls: List[VarDecl], *, data: Dict[str, Any]) -> Iterator[str]:
    last_type = None
    last_inits = []
    for decl in decls:
        type, ctor = _get_type_and_ctor(decl, data=data)
        if last_type != type and last_type is not None:
            yield f"""{last_type} {", ".join(last_inits)};"""
            last_inits = []
        last_type = type
        last_inits.append(f"""{decl.name}{ctor}""")
    if last_type is not None:
        yield f"""{type} {", ".join(last_inits)};"""


def _declare_constant(decl: ConstantDecl, *, data: Dict[str, Any]) -> str:
    if decl.type == VarType.String:
        const = "const"
    else:
        const = "constexpr"
    type = _get_base_type(decl.type, data=data)
    if decl.type == VarType.String:
        value = '"' + decl.value + '"'
    elif decl.type == VarType.Char:
        value = "'" + decl.value + "'"
    else:
        value = str(decl.value)
    return f"""{const} {type} {decl.name} = {value};"""


def _read_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[VarName, VarDecl], data: Dict[str, Any], make_node: Callable[[str, Optional[VarType]], CPlusPlusNode] = lambda var, type: InputNode(exprs=[(var, type)])) -> CPlusPlusNode:
    """
    :raises CPlusPlusGeneratorError:
    """

    # declare all possible variables
    new_decls: List[CPlusPlusNode] = []
    var: str
    for var, decl in decls.items():
        if var not in declared and all([dep in initialized for dep in decl.depending]):
            new_decls.append(DeclNode(decls=[decl]))
            declared.add(var)
    if new_decls:
        return SentencesNode(sentences=new_decls + [_read_input_dfs(node, declared=declared, initialized=initialized, decls=decls, data=data, make_node=make_node)])

    # traverse AST
    if isinstance(node, ItemNode):
        if node.name not in declared:
            raise CPlusPlusGeneratorError(f"""variable {node.name} is not declared yet""")
        initialized.add(node.name)
        decl = decls[node.name]
        var = _get_variable(decl=decls[node.name], indices=node.indices, decls=decls)
        return make_node(var, decl.type)
    elif isinstance(node, NewlineNode):
        return SentencesNode(sentences=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_read_input_dfs(item, declared=declared, initialized=initialized, decls=decls, data=data, make_node=make_node))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        declared.add(node.name)
        body = _read_input_dfs(node.body, declared=declared, initialized=initialized, decls=decls, data=data, make_node=make_node)
        result = RepeatNode(name=node.name, size=node.size, body=body)
        declared.remove(node.name)
        return result
    else:
        assert False


def _has_trailing_space(node: CPlusPlusNode) -> bool:
    if isinstance(node, OutputTokensNode):
        return node.end != ''
    elif isinstance(node, SentencesNode):
        if not node:
            return False
        else:
            return _has_trailing_space(node.sentences[-1])
    elif isinstance(node, RepeatNode):
        return _has_trailing_space(node.body)
    else:
        assert False


def _write_output_dfs(node: FormatNode, *, decls: Dict[VarName, VarDecl], data: Dict[str, Any]) -> CPlusPlusNode:
    """
    :raises CPlusPlusGeneratorError:
    """

    if isinstance(node, ItemNode):
        decl = decls[node.name]
        var = _get_variable(decl=decl, indices=node.indices, decls=decls)
        return OutputTokensNode(exprs=[(VarName(var), decl.type)], end='')
    elif isinstance(node, NewlineNode):
        return OutputTokensNode(exprs=[], end='\n')
    elif isinstance(node, SequenceNode):
        sentences = []
        for i, item in enumerate(node.items):
            sentence = _write_output_dfs(item, decls=decls, data=data)
            sentences.append(sentence)
            if i + 1 < len(node.items) and not _has_trailing_space(sentence):
                sentences.append(OutputTokensNode(exprs=[], end=' '))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        body = _write_output_dfs(node.body, decls=decls, data=data)
        if not _has_trailing_space(body):
            body = SentencesNode(sentences=[body, OutputTokensNode(exprs=[], end=' ')])
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
    elif isinstance(node, GenerateNode):
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
            elif sentences and isinstance(sentences[-1], OutputTokensNode) and sentences[-1].end != '\n' and isinstance(sentence, OutputTokensNode):
                sentences[-1].exprs.extend(sentence.exprs)
                sentences[-1].end = sentence.end
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
        yield from _read_variables(node.exprs, data=data)
    elif isinstance(node, OutputTokensNode):
        yield from _write_variables(node.exprs, end=node.end, data=data)
    elif isinstance(node, GenerateNode):
        yield from _generate_variable(node.expr, data=data)
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


def _read_input_fallback(message: str, *, data: Dict[str, Any], nest: int) -> str:
    lines = []
    lines.append(f"""// {message}""")
    lines.append(f"""// TODO: edit here""")
    lines.extend(_declare_variables([VarDecl(name=VarName('n'), type=VarType.IndexInt, dims=[], bases=[], depending=set())], data=data))
    lines.extend(_read_variables([('n', VarType.IndexInt)], data=data))
    lines.extend(_declare_variables([VarDecl(name=VarName('a'), type=VarType.ValueInt, dims=[Expr('n')], bases=[Expr('0')], depending=set([VarName('n')]))], data=data))
    lines.append(_declare_loop(var=VarName('i'), size=Expr('n'), data=data) + " {")
    lines.extend(_read_variables([('a[i]', VarType.ValueInt)], data=data))
    lines.append("""}""")
    return _join_with_indent(iter(lines), nest=nest, data=data)


def read_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return _read_input_fallback(message="failed to analyze input format", data=data, nest=nest)

    node = _read_input_dfs(analyzed.input_format, declared=set(), initialized=set(), decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def _generate_input_fallback(message: str, data: Dict[str, Any], *, nest: int = 1) -> str:
    lines = []
    lines.append(f"""// {message}""")
    lines.append(f"""// TODO: edit here""")
    lines.append(f"""std::random_device device;""")
    lines.append(f"""std::default_random_engine gen(device());""")
    lines.extend(_declare_variables([VarDecl(name=VarName('n'), type=VarType.IndexInt, dims=[], bases=[], depending=set())], data=data))
    lines.extend(_generate_variable(('n', VarType.IndexInt), data=data))
    lines.extend(_declare_variables([VarDecl(name=VarName('a'), type=VarType.ValueInt, dims=[Expr('n')], bases=[Expr('0')], depending=set([VarName('n')]))], data=data))
    lines.append(_declare_loop(var=VarName('i'), size='n', data=data) + " {")
    lines.extend(_generate_variable(('a[i]', VarType.ValueInt), data=data))
    lines.append("""}""")
    return _join_with_indent(iter(lines), nest=nest, data=data)


def generate_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return _generate_input_fallback(message="failed to analyze input format", data=data, nest=nest)

    make_node = lambda var, type: GenerateNode(expr=(var, type))
    node = _read_input_dfs(analyzed.input_format, declared=set(), initialized=set(), decls=analyzed.input_variables, data=data, make_node=make_node)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def _write_input_fallback(message: str, data: Dict[str, Any], *, nest: int = 1) -> str:
    lines = []
    lines.append(f"""// {message}""")
    lines.append(f"""// TODO: edit here""")
    lines.extend(_write_variables([('n', VarType.IndexInt)], end='\n', data=data))
    lines.append(_declare_loop(var=VarName('i'), size='n', data=data) + " {")
    lines.extend(_read_variables([('a[i]', VarType.ValueInt)], data=data))
    lines.append("""}""")
    return _join_with_indent(iter(lines), nest=nest, data=data)


def write_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    if data['config'].get('using_namespace_std') == False:
        logger.warning('Now `data["config"]["using_namespace_std"] = False` is deprecated and has no meaning.')

    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return _write_input_fallback(message="failed to analyze input format", data=data, nest=nest)

    node = _write_output_dfs(analyzed.input_format, decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def _write_output_fallback(message: str, *, data: Dict[str, Any], nest: int) -> str:
    lines = []
    lines.append(f"""// {message}""")
    lines.append(f"""// TODO: edit here""")
    lines.extend(_write_variables([('ans', VarType.ValueInt)], end='\n', data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def write_output(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    output_type = analyzed.output_type

    if isinstance(output_type, OneOutputType):
        node: CPlusPlusNode = OutputTokensNode(exprs=[(output_type.name, output_type.type)], end='\n')

    elif isinstance(output_type, TwoOutputType):
        sentences: List[CPlusPlusNode] = []
        sentences.append(OutputTokensNode(exprs=[(output_type.name1, output_type.type1)], end=''))
        if output_type.print_newline_after_item:
            sentences.append(OutputTokensNode(exprs=[], end='\n'))
        sentences.append(OutputTokensNode(exprs=[(output_type.name2, output_type.type2)], end='\n'))
        node = SentencesNode(sentences=sentences)

    elif isinstance(output_type, YesNoOutputType):
        expr = f"""({output_type.name} ? {output_type.yes} : {output_type.no})"""
        node = OutputTokensNode(exprs=[(expr, VarType.String)], end='\n')

    elif isinstance(output_type, VectorOutputType):
        inner_sentences: List[CPlusPlusNode] = []
        inner_sentences.append(OutputTokensNode(exprs=[(output_type.subscripted_name, output_type.type)], end=''))
        if output_type.print_newline_after_item:
            end = '\n'
        else:
            end = ' '
        inner_sentences.append(OutputTokensNode(exprs=[], end=end))

        sentences = []
        size = f"""({_get_base_type(VarType.IndexInt, data=data)}){output_type.name}.size()"""
        if output_type.print_size:
            sentences.append(OutputTokensNode(exprs=[(size, VarType.IndexInt)], end=''))
            if output_type.print_newline_after_size:
                sentences.append(OutputTokensNode(exprs=[], end='\n'))
        sentences.append(RepeatNode(name=output_type.counter_name, size=size, body=SentencesNode(sentences=inner_sentences)))
        if not output_type.print_newline_after_item:
            sentences.append(OutputTokensNode(exprs=[], end='\n'))
        node = SentencesNode(sentences=sentences)

    elif output_type is None:
        if analyzed.output_format is None or analyzed.output_variables is None:
            return _write_output_fallback(message="failed to analyze output format", data=data, nest=nest)
        else:
            node = _write_output_dfs(analyzed.output_format, decls=analyzed.output_variables, data=data)

    else:
        assert False

    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def formal_arguments(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return f"""int n, const std::vector<int64_t> &a"""

    decls = analyzed.input_variables
    decls = utils._filter_ignored_variables(decls, data=data)

    args = []
    for name, decl in decls.items():
        type = _get_base_type(decl.type, data=data)
        for _ in reversed(decl.dims):
            space = ' ' if type.endswith('>') else ''
            type = f"""std::vector<{type}{space}>"""
        if decl.dims:
            type = f"""const {type} &"""
        args.append(f"""{type} {name}""".replace('& ', '&'))
    return ', '.join(args)


def actual_arguments(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return 'n, a'

    decls = analyzed.input_variables
    decls = utils._filter_ignored_variables(decls, data=data)
    return ', '.join(decls.keys())


def return_type(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    output_type = analyzed.output_type
    if isinstance(output_type, OneOutputType):
        return _get_base_type(output_type.type, data=data)
    elif isinstance(output_type, TwoOutputType):
        return f"""std::pair<{_get_base_type(output_type.type1, data=data)}, {_get_base_type(output_type.type2, data=data)}>"""
    elif isinstance(output_type, YesNoOutputType):
        return "bool"
    elif isinstance(output_type, VectorOutputType):
        return f"""std::vector<{_get_base_type(output_type.type, data=data)}>"""
    elif output_type is None:
        return "auto"
    else:
        assert False


def return_value(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    output_type = analyzed.output_type
    if isinstance(output_type, OneOutputType):
        return output_type.name
    elif isinstance(output_type, TwoOutputType):
        return f"""[{output_type.name1}, {output_type.name2}]"""
    elif isinstance(output_type, YesNoOutputType):
        return output_type.name
    elif isinstance(output_type, VectorOutputType):
        return output_type.name
    elif output_type is None:
        return "ans"
    else:
        assert False


def declare_constants(data: Dict[str, Any], *, nest: int = 0) -> str:
    analyzed = utils.get_analyzed(data)
    lines: List[str] = []
    for decl in analyzed.constants.values():
        lines.append(_declare_constant(decl, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)
