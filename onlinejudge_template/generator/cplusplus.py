"""
the module to generate C++ code

この module は C++ のコードを生成します。

以下の関数を提供します。

- :func:`read_input`
- :func:`write_output`
- :func:`declare_constants`
- :func:`arguments_types`
- :func:`arguments`
- :func:`return_type`
- :func:`return_values`

次のように利用することが想定されています。

.. code-block:: c++

    #include ...
    ...

    ${cplusplus.declare_constants(data)}
    ${cplusplus.return_type(data)} solve(${cplusplus.arguments_types(data)}) {
        ...
    }

    int main() {
    ${cplusplus.read_input(data)}
        ${cplusplus.return_type(data)} ${cplusplus.return_values(data)} = solve(${cplusplus.arguments(data)});
    ${cplusplus.write_output(data)}
    }
"""

import abc
from typing import *

import onlinejudge_template.generator.utils as utils
from onlinejudge_template.types import *
from onlinejudge_template.utils import simplify


class CPlusPlusGeneratorError(GeneratorError):
    pass


class CPlusPlusNode(abc.ABC):
    def __repr__(self) -> str:
        keys = dir(self)
        keys = list(filter(lambda key: not key.startswith('_'), keys))
        keys.sort()
        items = ', '.join([key + '=' + repr(getattr(self, key)) for key in keys])
        return f"{self.__class__.__name__}({items})"


class DeclNode(CPlusPlusNode):
    def __init__(self, decls: List[VarDecl]):
        self.decls = decls


class InputNode(CPlusPlusNode):
    def __init__(self, exprs: List[Tuple[str, Optional[VarType]]]):
        self.exprs = exprs


class OutputTokensNode(CPlusPlusNode):
    def __init__(self, exprs: List[Tuple[str, Optional[VarType]]]):
        self.exprs = exprs


class OutputNewlineNode(CPlusPlusNode):
    def __init__(self, exprs: List[Tuple[str, Optional[VarType]]]):
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
    indent = utils.get_indent(data=data)
    buf = []
    for line in lines:
        if line.startswith('}'):
            nest -= 1
        buf.append(indent * nest + line)
        if line.endswith('{'):
            nest += 1
    return '\n'.join(buf)


def _declare_loop(var: str, size: str, *, data: Dict[str, Any]) -> str:
    """
    :raises CPlusPlusGeneratorError"
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
    :raises CPlusPlusGeneratorError"
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
        items.append(f"""{_get_std(data=data)}cin""")
        for expr, _ in exprs:
            items.append(expr)
        return [" >> ".join(items) + ";"]
    elif callable(scanner):
        return scanner(exprs)
    else:
        raise CPlusPlusGeneratorError(f"""invalid "scanner" config: {scanner}""")


def _write_variables(exprs: List[Tuple[str, Optional[VarType]]], *, newline: bool, data: Dict[str, Any]) -> List[str]:
    """
    :raises CPlusPlusGeneratorError"
    """

    printer = data['config'].get('printer')
    if printer == 'printf':
        specifiers = ''
        arguments = ['']
        for expr, type in exprs:
            specifiers += _get_base_type_format_specifier(type, name=expr, data=data)
            arguments.append(expr)
        return [f"""printf("{specifiers}\\n"{', '.join(arguments)});"""]
    elif printer is None or printer in ('cout', 'std::cout'):
        items = []
        items.append(f"""{_get_std(data=data)}cout""")
        for i, (expr, _) in enumerate(exprs):
            if i:
                items.append("""' '""")
            items.append(expr)
        items.append(f"""{_get_std(data=data)}endl""")
        return [" << ".join(items) + ";"]
    elif callable(printer):
        return printer(exprs, newline=newline)
    else:
        raise CPlusPlusGeneratorError(f"""invalid "printer" config: {printer}""")


def _get_std(data: Dict['str', Any]) -> str:
    if data['config'].get('using_namespace_std'):
        return ''
    else:
        return 'std::'


def _get_base_type(type: Optional[VarType], *, data: Dict[str, Any]) -> str:
    if type == VarType.IndexInt:
        return "int"
    elif type == VarType.ValueInt:
        return data['config'].get('long_long_int', "long long")
    elif type == VarType.Float:
        return "double"
    elif type == VarType.String:
        return f"""{_get_std(data=data)}string"""
    elif type == VarType.Char:
        return "char"
    elif type is None:
        return "auto"
    else:
        assert False


def _get_base_type_format_specifier(type: Optional[VarType], *, name: str, data: Dict[str, Any]) -> str:
    """
    :raises CPlusPlusGeneratorError"
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
        type = f"""{_get_std(data=data)}vector<{type}{space}>"""
    return type, ctor


def _get_variable(*, decl: VarDecl, indices: List[str], decls: Dict[str, VarDecl]) -> str:
    var = decl.name
    for index, base in zip(indices, decl.bases):
        i = simplify(f"""{index} - ({base})""", env=set(decls.keys()))
        var = f"""{var}[{i}]"""
    return var


def _declare_variables(decls: List[VarDecl], *, data: Dict[str, Any]) -> Iterator[str]:
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


def _read_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, VarDecl], data: Dict[str, Any]) -> CPlusPlusNode:
    """
    :raises CPlusPlusGeneratorError"
    """

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
            raise CPlusPlusGeneratorError(f"""variable {node.name} is not declared yet""")
        initialized.add(node.name)
        decl = decls[node.name]
        var = _get_variable(decl=decls[node.name], indices=node.indices, decls=decls)
        return InputNode(exprs=[(var, decl.type)])
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


def _write_output_dfs(node: FormatNode, *, decls: Dict[str, VarDecl], data: Dict[str, Any]) -> CPlusPlusNode:
    """
    :raises CPlusPlusGeneratorError"
    """

    if isinstance(node, ItemNode):
        decl = decls[node.name]
        var = _get_variable(decl=decl, indices=node.indices, decls=decls)
        return OutputTokensNode(exprs=[(var, decl.type)])
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


class OutputType(abc.ABC):
    pass


class YesNoOutputType(OutputType):
    name: str
    yes: str
    no: str

    def __init__(self, *, name: str, yes: str, no: str):
        self.name = name
        self.yes = yes
        self.no = no


class OneOutputType(OutputType):
    name: str
    type: VarType

    def __init__(self, *, name: str, type: VarType):
        self.name = name
        self.type = type


class TwoOutputType(OutputType):
    name1: str
    type1: VarType
    name2: str
    type2: VarType
    print_newline_after_item: bool

    def __init__(self, *, name1: str, type1: VarType, name2: str, type2: VarType, print_newline_after_item: bool):
        self.name1 = name1
        self.type1 = type1
        self.name2 = name2
        self.type2 = type2
        self.print_newline_after_item = print_newline_after_item


class VectorOutputType(OutputType):
    name: str
    type: VarType
    subscripted_name: str
    counter_name: str
    print_size: bool
    print_newline_after_size: bool
    print_newline_after_item: bool

    def __init__(self, *, name: str, type: VarType, subscripted_name: str, counter_name: str, print_size: bool, print_newline_after_size: bool, print_newline_after_item: bool):
        self.name = name
        self.type = type
        self.subscripted_name = subscripted_name
        self.counter_name = counter_name
        self.print_size = print_size
        self.print_newline_after_size = print_newline_after_size
        self.print_newline_after_item = print_newline_after_item


class UnknownOutputType(OutputType):
    pass


def _analyze_output_type(*, data: Dict[str, Any]) -> OutputType:
    analyzed = utils.get_analyzed(data)
    if analyzed.output_format is None or analyzed.output_variables is None:
        return UnknownOutputType()
    node = analyzed.output_format
    decls = analyzed.output_variables

    if isinstance(node, SequenceNode) and len(node.items) == 2:
        item0 = node.items[0]
        item1 = node.items[1]
        if isinstance(item0, ItemNode) and isinstance(item1, NewlineNode):
            type = decls[item0.name].type
            name = 'ans'  # item0.name may be randomized
            if type is not None:
                if 'YES' in analyzed.constants and 'NO' in analyzed.constants and type == VarType.String:
                    return YesNoOutputType(name=name, yes='YES', no='NO')
                if 'FIRST' in analyzed.constants and 'SECOND' in analyzed.constants and type == VarType.String:
                    return YesNoOutputType(name=name, yes='FIRST', no='SECOND')
                return OneOutputType(name=name, type=type)

    if isinstance(node, SequenceNode) and len(node.items) == 3:
        item0 = node.items[0]
        item1 = node.items[1]
        item2 = node.items[2]
        if isinstance(item0, ItemNode) and isinstance(item1, ItemNode) and isinstance(item2, NewlineNode):
            name1 = item0.name
            name2 = item1.name
            type1 = decls[name1].type
            type2 = decls[name2].type
            if type1 is not None and type2 is not None:
                return TwoOutputType(name1=name1, type1=type1, name2=name2, type2=type2, print_newline_after_item=False)

    if isinstance(node, SequenceNode) and len(node.items) == 4:
        item0 = node.items[0]
        item1 = node.items[1]
        item2 = node.items[2]
        item3 = node.items[3]
        if isinstance(item0, ItemNode) and isinstance(item1, NewlineNode) and isinstance(item2, ItemNode) and isinstance(item3, NewlineNode):
            name1 = item0.name
            name2 = item2.name
            type1 = decls[name1].type
            type2 = decls[name2].type
            if type1 is not None and type2 is not None:
                return TwoOutputType(name1=name1, type1=type1, name2=name2, type2=type2, print_newline_after_item=False)

    if isinstance(node, SequenceNode) and len(node.items) == 4:
        item0 = node.items[0]
        item1 = node.items[1]
        item2 = node.items[2]
        item3 = node.items[3]
        if isinstance(item0, ItemNode) and isinstance(item1, NewlineNode) and isinstance(item3, NewlineNode):
            if isinstance(item2, LoopNode) and isinstance(item2.body, ItemNode) and item2.size == item0.name and item2.body.indices == [item2.name]:
                type = decls[item2.body.name].type
                name = 'ans'  # item2.body.name may be randomized
                subscripted_name = _get_variable(decl=decls[name], indices=item2.body.indices, decls=decls)
                counter_name = item2.name
                if type is not None:
                    return VectorOutputType(name=name, type=type, subscripted_name=subscripted_name, counter_name=counter_name, print_size=True, print_newline_after_size=True, print_newline_after_item=False)

    if isinstance(node, SequenceNode) and len(node.items) == 3:
        item0 = node.items[0]
        item1 = node.items[1]
        item2 = node.items[2]
        if isinstance(item0, ItemNode) and isinstance(item1, NewlineNode):
            if isinstance(item2, LoopNode) and isinstance(item2.body, SequenceNode) and len(item2.body.items) == 2:
                item3 = node.items[0]
                item4 = node.items[1]
                if isinstance(item3, ItemNode) and isinstance(item4, NewlineNode) and item2.size == item0.name and item3.indices == [item0.name]:
                    type = decls[item3.name].type
                    name = 'ans'  # item3.name may be randomized
                    subscripted_name = _get_variable(decl=decls[name], indices=item3.indices, decls=decls)
                    counter_name = item2.name
                    if type is not None:
                        return VectorOutputType(name=name, type=type, subscripted_name=subscripted_name, counter_name=counter_name, print_size=True, print_newline_after_size=True, print_newline_after_item=True)

    return UnknownOutputType()


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
        yield from _read_variables(node.exprs, data=data)
    elif isinstance(node, OutputTokensNode):
        yield from _write_variables(node.exprs, newline=False, data=data)
    elif isinstance(node, OutputNewlineNode):
        yield from _write_variables(node.exprs, newline=True, data=data)
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
    try:
        lines.extend(_declare_variables([VarDecl(name='n', type=VarType.IndexInt, dims=[], bases=[], depending=set())], data=data))
    except CPlusPlusGeneratorError:
        lines.append(f"""int n;""")
    try:
        lines.extend(_read_variables([('n', VarType.IndexInt)], data=data))
    except CPlusPlusGeneratorError:
        lines.append(f"""{_get_std(data=data)}scanf("%d", &n);""")
    try:
        lines.extend(_declare_variables([VarDecl(name='a', type=VarType.ValueInt, dims=['n'], bases=['0'], depending=set(['n']))], data=data))
    except CPlusPlusGeneratorError:
        lines.append(f"""{_get_std(data=data)}vector<int> a(n);""")
    try:
        lines.append(_declare_loop(var='i', size='n', data=data) + " {")
    except CPlusPlusGeneratorError:
        lines.append("""for (int i = 0; i < n; ++i) {""")
    try:
        lines.extend(_read_variables([('a[i]', VarType.ValueInt)], data=data))
    except CPlusPlusGeneratorError:
        lines.append(f"""{_get_std(data=data)}scanf("%d", &a[i]);""")
    lines.append("""}""")
    return _join_with_indent(iter(lines), nest=nest, data=data)


def read_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return _read_input_fallback(message="failed to analyze input format", data=data, nest=nest)

    try:
        node = _read_input_dfs(analyzed.input_format, declared=set(), initialized=set(), decls=analyzed.input_variables, data=data)
    except CPlusPlusGeneratorError as e:
        return _read_input_fallback(message="failed to generate input part: " + str(e), data=data, nest=nest)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def _write_output_fallback(message: str, *, data: Dict[str, Any], nest: int) -> str:
    lines = []
    lines.append(f"""// {message}""")
    lines.append(f"""// TODO: edit here""")
    try:
        lines.extend(_write_variables([('ans', VarType.ValueInt)], newline=True, data=data))
    except CPlusPlusGeneratorError:
        lines.append(f"""{_get_std(data=data)}printf("%d\n", ans);""")
    return _join_with_indent(iter(lines), nest=nest, data=data)


def write_output(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.output_format is None or analyzed.output_variables is None:
        return _write_output_fallback(message="failed to analyze output format", data=data, nest=nest)
    output_type = _analyze_output_type(data=data)

    if isinstance(output_type, OneOutputType):
        node: CPlusPlusNode = OutputNewlineNode(exprs=[(output_type.name, output_type.type)])

    elif isinstance(output_type, TwoOutputType):
        sentences: List[CPlusPlusNode] = []
        sentences.append(OutputTokensNode(exprs=[(output_type.name1, output_type.type1)]))
        if output_type.print_newline_after_item:
            sentences.append(OutputNewlineNode(exprs=[]))
        sentences.append(OutputNewlineNode(exprs=[(output_type.name2, output_type.type2)]))
        node = SentencesNode(sentences=sentences)

    elif isinstance(output_type, YesNoOutputType):
        expr = f"""({output_type.name} ? {output_type.yes} : {output_type.no})"""
        node = OutputNewlineNode(exprs=[(expr, VarType.String)])

    elif isinstance(output_type, VectorOutputType):
        inner_sentences: List[CPlusPlusNode] = []
        inner_sentences.append(OutputTokensNode(exprs=[(output_type.subscripted_name, output_type.type)]))
        if output_type.print_newline_after_item:
            inner_sentences.append(OutputNewlineNode(exprs=[]))

        sentences = []
        size = f"""({_get_base_type(VarType.IndexInt, data=data)}){output_type.name}.size()"""
        if output_type.print_size:
            sentences.append(OutputTokensNode(exprs=[(size, VarType.IndexInt)]))
            if output_type.print_newline_after_size:
                sentences.append(OutputNewlineNode(exprs=[]))
        sentences.append(RepeatNode(name=output_type.counter_name, size=size, body=SentencesNode(sentences=inner_sentences)))
        if not output_type.print_newline_after_item:
            inner_sentences.append(OutputNewlineNode(exprs=[]))
        node = SentencesNode(sentences=sentences)

    elif isinstance(output_type, UnknownOutputType):
        try:
            node = _write_output_dfs(analyzed.output_format, decls=analyzed.output_variables, data=data)
        except CPlusPlusGeneratorError as e:
            return _write_output_fallback(message="failed to generate output part: " + str(e), data=data, nest=nest)

    else:
        assert False

    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)


def arguments_types(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return f"""int n, const {_get_std(data=data)}<int> & a"""

    args = []
    for name, decl in analyzed.input_variables.items():
        type = _get_base_type(decl.type, data=data)
        for _ in reversed(decl.dims):
            space = ' ' if type.endswith('>') else ''
            type = f"""{_get_std(data=data)}vector<{type}{space}>"""
        if decl.dims:
            type = f"""const {type} &"""
        args.append(f"""{type} {name}""")
    return ', '.join(args)


def arguments(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return 'n, a'

    return ', '.join(analyzed.input_variables.keys())


def return_type(data: Dict[str, Any]) -> str:
    output_type = _analyze_output_type(data=data)
    if isinstance(output_type, OneOutputType):
        return _get_base_type(output_type.type, data=data)
    elif isinstance(output_type, TwoOutputType):
        return f"""{_get_std(data=data)}pair<{_get_base_type(output_type.type1, data=data)}, {_get_base_type(output_type.type2, data=data)}>"""
    elif isinstance(output_type, YesNoOutputType):
        return "bool"
    elif isinstance(output_type, VectorOutputType):
        return f"""{_get_std(data=data)}vector<{_get_base_type(output_type.type, data=data)}>"""
    elif isinstance(output_type, UnknownOutputType):
        return "auto"
    else:
        assert False


def return_values(data: Dict[str, Any]) -> str:
    output_type = _analyze_output_type(data=data)
    if isinstance(output_type, OneOutputType):
        return output_type.name
    elif isinstance(output_type, TwoOutputType):
        return f"""[{output_type.name1}, {output_type.name2}]"""
    elif isinstance(output_type, YesNoOutputType):
        return output_type.name
    elif isinstance(output_type, VectorOutputType):
        return output_type.name
    elif isinstance(output_type, UnknownOutputType):
        return "ans"
    else:
        assert False


def declare_constants(data: Dict[str, Any], *, nest: int = 0) -> str:
    analyzed = utils.get_analyzed(data)
    lines: List[str] = []
    for decl in analyzed.constants.values():
        lines.append(_declare_constant(decl, data=data))
    return _join_with_indent(iter(lines), nest=nest, data=data)
