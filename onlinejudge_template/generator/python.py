"""
the module to generate Python code

この module は Python のコードを生成します。

以下の関数を提供します。

- :func:`read_input`
- :func:`write_output`
- :func:`declare_constants`
- :func:`formal_arguments`
- :func:`actual_arguments`
- :func:`return_type`
- :func:`return_value`

加えて、ランダムケースの生成のために、以下の関数を提供します。

- :func:`generate_input`
- :func:`write_input`
"""

from typing import *

import onlinejudge_template.generator._utils as utils
from onlinejudge_template.generator._python import *
from onlinejudge_template.types import *
from onlinejudge_template.utils import simplify

_DEDENT = '*DEDENT*'


def _join_with_indent(lines: Sequence[str], *, nest: int, data: Dict[str, Any]) -> str:
    indent = data['config'].get('indent', ' ' * 4)
    buf = []
    for line in lines:
        if line == _DEDENT:
            nest -= 1
            continue
        buf.append(indent * nest + line)
        if line.endswith(':'):
            nest += 1
    return '\n'.join(buf)


def _get_python_type(type: Optional[VarType]) -> str:
    if type == VarType.IndexInt:
        return "int"
    elif type == VarType.ValueInt:
        return "int"
    elif type == VarType.Float:
        return "float"
    elif type == VarType.String:
        return "str"
    elif type == VarType.Char:
        return "str"
    elif type is None:
        return "str"
    else:
        assert False


def _get_variable(*, decl: VarDecl, indices: List[str]) -> str:
    var = decl.name
    for index, base in zip(indices, decl.bases):
        i = simplify(f"""{index} - ({base})""")
        var = f"""{var}[{i}]"""
    return var


def _declare_variable(name: str, dims: List[str], *, data: Dict[str, Any]) -> Iterator[str]:
    if dims:
        ctor = "None"
        for dim in reversed(dims):
            ctor = f"""[{ctor} for _ in range({dim})]"""
        yield f"""{name} = {ctor}"""


def _declare_all_possible_variables(declared: Set[str], initialized: Set[str], decls: Dict[str, VarDecl], data: Dict[str, Any]) -> List[PythonNode]:
    """
    :param declared: updated
    """

    decl_nodes: List[PythonNode] = []
    for var, decl in decls.items():
        if var not in declared and all([dep in initialized for dep in decl.depending]):
            for line in _declare_variable(var, decl.dims, data=data):
                decl_nodes.append(OtherNode(line=line))
            declared.add(var)
    return decl_nodes


def _declare_constant(decl: ConstantDecl, *, data: Dict[str, Any]) -> str:
    if decl.type in (VarType.String, VarType.Char):
        value = repr(decl.value)
    else:
        value = decl.value
    return f"""{decl.name} = {value}"""


def _generate_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    decl_nodes = _declare_all_possible_variables(declared=declared, initialized=initialized, decls=decls, data=data)
    if decl_nodes:
        return SentencesNode(sentences=decl_nodes + [_generate_input_dfs(node, declared=declared, initialized=initialized, decls=decls, data=data)])

    # traverse AST
    if isinstance(node, ItemNode):
        var = _get_variable(decl=decls[node.name], indices=node.indices)
        type_ = decls[node.name].type
        initialized.add(node.name)
        if type_ == VarType.IndexInt:
            return OtherNode(line=f"""{var} = random.randint(1, 1000)  # TODO: edit here""")
        elif type_ == VarType.ValueInt:
            return OtherNode(line=f"""{var} = random.randint(1, 10 ** 9)  # TODO: edit here""")
        elif type_ == VarType.Float:
            return OtherNode(line=f"""{var} = 100.0 * random.random()  # TODO: edit here""")
        elif type_ == VarType.String:
            return OtherNode(line=f"""{var} = ''.join([random.choice('abcde') for range(random.randint(1, 100))])  # TODO: edit here""")
        elif type_ == VarType.Char:
            return OtherNode(line=f"""{var} = random.choice('abcde')  # TODO: edit here""")
        else:
            return OtherNode(line=f"""{var} = None  # TODO: edit here""")
    elif isinstance(node, NewlineNode):
        return SentencesNode(sentences=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_generate_input_dfs(item, declared=declared, initialized=initialized, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        declared.add(node.name)
        body = _generate_input_dfs(node.body, declared=declared, initialized=initialized, decls=decls, data=data)
        declared.remove(node.name)
        return RangeNode(name=node.name, size=node.size, body=body)
    else:
        assert False


def _read_input_dfs(node: FormatNode, *, decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    if isinstance(node, ItemNode):
        decl = decls[node.name]
        var = _get_variable(decl=decl, indices=node.indices)
        return InputTokensNode(exprs=[(var, decl)])
    elif isinstance(node, NewlineNode):
        return InputNode(exprs=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_read_input_dfs(item, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        return RangeNode(name=node.name, size=node.size, body=_read_input_dfs(node.body, decls=decls, data=data))
    else:
        assert False


def _write_output_dfs(node: FormatNode, *, decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    if isinstance(node, ItemNode):
        var = _get_variable(decl=decls[node.name], indices=node.indices)
        return PrintTokensNode(exprs=[var])
    elif isinstance(node, NewlineNode):
        return PrintNode(exprs=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_write_output_dfs(item, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        return RangeNode(name=node.name, size=node.size, body=_write_output_dfs(node.body, decls=decls, data=data))
    else:
        assert False


def _optimize_syntax_tree(node: PythonNode, *, data: Dict[str, Any]) -> PythonNode:
    if isinstance(node, InputTokensNode):
        return node
    elif isinstance(node, InputNode):
        return node
    elif isinstance(node, PrintTokensNode):
        return node
    elif isinstance(node, PrintNode):
        return node
    elif isinstance(node, SentencesNode):
        sentences: List[PythonNode] = []
        que: List[PythonNode] = [_optimize_syntax_tree(sentence, data=data) for sentence in node.sentences]
        while que:
            sentence: PythonNode = que[0]
            que = que[1:]
            if sentences:
                last: Optional[PythonNode] = sentences[-1]
            else:
                last = None
            if isinstance(last, InputTokensNode) and isinstance(sentence, InputNode):
                sentence = InputNode(exprs=last.exprs + sentence.exprs)
                sentences.pop()
                que = [sentence] + que  # type: ignore
            elif isinstance(last, PrintTokensNode) and isinstance(sentence, PrintNode):
                sentence = PrintNode(exprs=last.exprs + sentence.exprs)
                sentences.pop()
                que = [sentence] + que  # type: ignore
            elif isinstance(last, RangeNode) and isinstance(last.body, PrintTokensNode) and len(last.body.exprs) == 1 and isinstance(sentence, PrintNode):
                array = f"""*[{last.body.exprs[0]} for {last.name} in range({last.size})]"""
                sentence = PrintNode(exprs=[array] + sentence.exprs)
                sentences.pop()
                que = [sentence] + que  # type: ignore
            elif isinstance(sentence, SentencesNode):
                que = sentence.sentences + que
            else:
                sentences.append(sentence)
        return SentencesNode(sentences=sentences)
    elif isinstance(node, RangeNode):
        return RangeNode(name=node.name, size=node.size, body=_optimize_syntax_tree(node.body, data=data))
    elif isinstance(node, OtherNode):
        return node
    else:
        assert False


def _realize_input_nodes_without_tokens(node: PythonNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    """
    :raises TokenizedInputRequiredError:
    """

    decl_nodes = _declare_all_possible_variables(declared=declared, initialized=initialized, decls=decls, data=data)
    if decl_nodes:
        return SentencesNode(sentences=decl_nodes + [_realize_input_nodes_without_tokens(node, declared=declared, initialized=initialized, decls=decls, data=data)])

    if isinstance(node, InputTokensNode):
        raise TokenizedInputRequiredError

    elif isinstance(node, InputNode):
        for _, decl in node.exprs:
            initialized.add(decl.name)

        if len(node.exprs) == 0:
            return OtherNode(line="""assert input() == ''""")
        elif len(node.exprs) == 1:
            expr, decl = node.exprs[0]
            if _get_python_type(decl.type) == "str":
                return OtherNode(line=f"""{expr} = input()""")
            else:
                return OtherNode(line=f"""{expr} = {_get_python_type(decl.type)}(input())""")
        else:
            exprs = [expr for expr, _ in node.exprs]
            types = [decl.type for _, decl in node.exprs]
            if len(set(map(_get_python_type, types))) == 1:
                type = types[0]
                if _get_python_type(type) == "str":
                    return OtherNode(line=f"""{', '.join(exprs)} = input().split()""")
                else:
                    return OtherNode(line=f"""{', '.join(exprs)} = map({_get_python_type(type)}, input().split())""")
            else:
                raise TokenizedInputRequiredError

    elif isinstance(node, PrintTokensNode):
        return node
    elif isinstance(node, PrintNode):
        return node
    elif isinstance(node, SentencesNode):
        sentences: List[PythonNode] = []
        for sentence in node.sentences:
            sentences.append(_realize_input_nodes_without_tokens(sentence, declared=declared, initialized=initialized, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, RangeNode):
        declared.add(node.name)
        body = _realize_input_nodes_without_tokens(node.body, declared=declared, initialized=initialized, decls=decls, data=data)
        declared.remove(node.name)
        return RangeNode(name=node.name, size=node.size, body=body)
    elif isinstance(node, OtherNode):
        return node
    else:
        assert False


def _realize_input_nodes_with_tokens_dfs(node: PythonNode, tokens: str, *, declared: Set[str], initialized: Set[str], decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    decl_nodes = _declare_all_possible_variables(declared=declared, initialized=initialized, decls=decls, data=data)
    if decl_nodes:
        return SentencesNode(sentences=decl_nodes + [_realize_input_nodes_with_tokens_dfs(node, tokens, declared=declared, initialized=initialized, decls=decls, data=data)])

    if isinstance(node, InputTokensNode) or isinstance(node, InputNode):
        for _, decl in node.exprs:
            initialized.add(decl.name)

        sentences: List[PythonNode] = []
        for expr, decl in node.exprs:
            if _get_python_type(decl.type) == "str":
                node_ = OtherNode(line=f"""{expr} = next({tokens})""")
            else:
                node_ = OtherNode(line=f"""{expr} = {_get_python_type(decl.type)}(next({tokens}))""")
            sentences.append(node_)
        return SentencesNode(sentences=sentences)

    elif isinstance(node, PrintTokensNode):
        return node
    elif isinstance(node, PrintNode):
        return node
    elif isinstance(node, SentencesNode):
        sentences = []
        for sentence in node.sentences:
            sentences.append(_realize_input_nodes_with_tokens_dfs(sentence, tokens, declared=declared, initialized=initialized, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, RangeNode):
        declared.add(node.name)
        body = _realize_input_nodes_with_tokens_dfs(node.body, tokens, declared=declared, initialized=initialized, decls=decls, data=data)
        declared.remove(node.name)
        return RangeNode(name=node.name, size=node.size, body=body)
    elif isinstance(node, OtherNode):
        return node
    else:
        assert False


def _realize_input_nodes_with_tokens(node: PythonNode, tokens: str, *, decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    node = SentencesNode(sentences=[
        OtherNode(line="""import sys"""),
        OtherNode(line=f"""{tokens} = iter(sys.stdin.read().split())"""),
        node,
        OtherNode(line=f"""assert next({tokens}, None) is None"""),
    ])
    return _realize_input_nodes_with_tokens_dfs(node, tokens, declared=set(), initialized=set(), decls=decls, data=data)


def _serialize_syntax_tree(node: PythonNode, *, data: Dict[str, Any]) -> Iterator[str]:
    if isinstance(node, InputTokensNode):
        assert False
    elif isinstance(node, InputNode):
        assert False
    elif isinstance(node, PrintTokensNode):
        if node.exprs:
            yield f"""print({', '.join(node.exprs)}, end=' ')"""
    elif isinstance(node, PrintNode):
        yield f"""print({', '.join(node.exprs)})"""
    elif isinstance(node, SentencesNode):
        for item in node.sentences:
            yield from _serialize_syntax_tree(item, data=data)
    elif isinstance(node, RangeNode):
        yield f"""for {node.name} in range({node.size}):"""
        yield from _serialize_syntax_tree(node.body, data=data)
        yield _DEDENT
    elif isinstance(node, OtherNode):
        yield node.line
    else:
        assert False


def generate_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        lines = [
            '# failed to analyze input format',
            'n = random.randint(1, 10 ** 9)  # TODO: edit here',
            'a = [random.randint(1, 10 ** 9) for _ in range(n)]  # TODO: edit here',
        ]
        return _join_with_indent(lines, nest=nest, data=data)

    node = _generate_input_dfs(analyzed.input_format, declared=set(), initialized=set(), decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(lines, nest=nest, data=data)


def write_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        lines = [
            'print(n)  # TODO: edit here',
            'print(*a)  # TODO: edit here',
        ]
        return _join_with_indent(lines, nest=nest, data=data)

    node = _write_output_dfs(analyzed.input_format, decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(lines, nest=nest, data=data)


def write_output(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.output_format is None or analyzed.output_variables is None:
        lines = [
            'print(ans)  # TODO: edit here',
        ]
        return _join_with_indent(lines, nest=nest, data=data)

    node = _write_output_dfs(analyzed.output_format, decls=analyzed.output_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(lines, nest=nest, data=data)


def read_input(data: Dict[str, Any], *, nest: int = 1) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        lines = [
            '# failed to analyze input format',
            'n = int(input())  # TODO: edit here',
            'a = list(map(int, input().split()))  # TODO: edit here',
        ]
        return _join_with_indent(lines, nest=nest, data=data)

    node = _read_input_dfs(analyzed.input_format, decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    try:
        node = _realize_input_nodes_without_tokens(node, declared=set(), initialized=set(), decls=analyzed.input_variables, data=data)
    except TokenizedInputRequiredError:
        node = _realize_input_nodes_with_tokens(node, 'tokens', decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(lines, nest=nest, data=data)


def formal_arguments(data: Dict[str, Any], *, typed: bool = True) -> str:
    if not typed:
        return actual_arguments(data=data)

    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return 'n: int, a: List[int]'

    args: List[str] = []
    for name, decl in analyzed.input_variables.items():
        type = _get_python_type(decl.type)
        for _ in decl.dims:
            type = f"""List[{type}]"""
        args.append(f"""{name}: {type}""")
    return ', '.join(args)


def actual_arguments(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.input_format is None or analyzed.input_variables is None:
        return 'n, a'

    return ', '.join(analyzed.input_variables.keys())


def return_type(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.output_format is None or analyzed.output_variables is None:
        return 'Any'

    types: List[str] = []
    for decl in analyzed.output_variables.values():
        type = _get_python_type(decl.type)
        for _ in decl.dims:
            type = f"""List[{type}]"""
        types.append(type)
    if len(types) == 0:
        return "None"
    elif len(types) == 1:
        return types[0]
    else:
        return f"""Tuple[{", ".join(types)}]"""


def return_value(data: Dict[str, Any]) -> str:
    analyzed = utils.get_analyzed(data)
    if analyzed.output_format is None or analyzed.output_variables is None:
        return 'ans'

    return ', '.join(analyzed.output_variables.keys())


def declare_constants(data: Dict[str, Any], *, nest: int = 0) -> str:
    analyzed = utils.get_analyzed(data)
    lines: List[str] = []
    for decl in analyzed.constants.values():
        lines.append(_declare_constant(decl, data=data))
    return _join_with_indent(lines, nest=nest, data=data)
