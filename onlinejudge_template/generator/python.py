"""
the module to generate Python code

この module は Python のコードを生成します。

以下の関数を提供します。

- :func:`generate_input`
- :func:`write_input`
"""

from typing import *

import onlinejudge_template.generator.utils as utils
from onlinejudge_template.types import *
from onlinejudge_template.utils import simplify


class PythonNode(abc.ABC):
    def __repr__(self) -> str:
        keys = dir(self)
        keys = list(filter(lambda key: not key.startswith('_'), keys))
        keys.sort()
        items = ', '.join([key + '=' + repr(getattr(self, key)) for key in keys])
        return f"{self.__class__.__name__}({items})"


class DeclNode(PythonNode):
    def __init__(self, decl: VarDecl):
        self.decl = decl


class InputTokensNode(PythonNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class InputNode(PythonNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class PrintTokensNode(PythonNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class PrintNode(PythonNode):
    def __init__(self, exprs: List[str]):
        self.exprs = exprs


class SentencesNode(PythonNode):
    def __init__(self, sentences: List[PythonNode]):
        self.sentences = sentences


class RangeNode(PythonNode):
    def __init__(self, name: str, size: str, body: PythonNode):
        self.name = name
        self.size = size
        self.body = body


class OtherNode(PythonNode):
    def __init__(self, line: str):
        self.line = line


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


def _generate_input_dfs(node: FormatNode, *, declared: Set[str], initialized: Set[str], decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    # declare all possible variables
    new_decls: List[PythonNode] = []
    for var, decl in decls.items():
        if var not in declared and all([dep in initialized for dep in decl.depending]):
            for line in _declare_variable(var, decl.dims, data=data):
                new_decls.append(OtherNode(line=line))
            declared.add(var)
    if new_decls:
        return SentencesNode(sentences=new_decls + [_generate_input_dfs(node, declared=declared, initialized=initialized, decls=decls, data=data)])

    # traverse AST
    if isinstance(node, ItemNode):
        var = _get_variable(decl=decls[node.name], indices=node.indices)
        initialized.add(node.name)
        return OtherNode(line=f"""{var} = random.randint(1, 10 ** 9)  # TODO: edit here""")
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


def _write_input_dfs(node: FormatNode, *, decls: Dict[str, VarDecl], data: Dict[str, Any]) -> PythonNode:
    if isinstance(node, ItemNode):
        var = _get_variable(decl=decls[node.name], indices=node.indices)
        return PrintTokensNode(exprs=[var])
    elif isinstance(node, NewlineNode):
        return PrintNode(exprs=[])
    elif isinstance(node, SequenceNode):
        sentences = []
        for item in node.items:
            sentences.append(_write_input_dfs(item, decls=decls, data=data))
        return SentencesNode(sentences=sentences)
    elif isinstance(node, LoopNode):
        return RangeNode(name=node.name, size=node.size, body=_write_input_dfs(node.body, decls=decls, data=data))
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


def _serialize_syntax_tree(node: PythonNode, *, data: Dict[str, Any]) -> Iterator[str]:
    if isinstance(node, InputTokensNode):
        raise NotImplementedError
    elif isinstance(node, InputNode):
        if len(node.exprs) == 0:
            yield f"""assert input() == ''"""
        elif len(node.exprs) == 1:
            yield f"""{node.exprs[0]} = int(input())"""
        if len(node.exprs) == 1:
            yield f"""{', '.join(node.exprs)}) = map(int, input().split())"""
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

    node = _write_input_dfs(analyzed.input_format, decls=analyzed.input_variables, data=data)
    node = _optimize_syntax_tree(node, data=data)
    lines = list(_serialize_syntax_tree(node, data=data))
    return _join_with_indent(lines, nest=nest, data=data)
