"""
the module to match format trees and sample strings

この module はフォーマット木とサンプル文字列がマッチするか判定し、マッチするならその結果を求めます。
たとえば
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N",
            item("A", indices="i")
        ),
        newline(),
    ])

のようなフォーマット木 (:any:`FormatNode`) と
::

    6
    1 3 8 7 10 2

というサンプル文字列が与えられれば
::

    {
        "N": 6,
        "A": [1, 3, 8, 7, 10, 2],
    }

に相当する結果を返します。
"""

from logging import getLogger
from typing import *

from onlinejudge_template.analyzer.simplify import evaluate
from onlinejudge_template.types import *

logger = getLogger(__name__)


class FormatMatchError(AnalyzerError):
    pass


def _get_env(values: Dict[VarName, Dict[Tuple[int, ...], Union[int, float, str]]]) -> Dict[VarName, Union[int, List[int], List[List[int]]]]:
    env: Dict[VarName, Union[int, List[int], List[List[int]]]] = {}
    for name, value in values.items():
        if () in value and isinstance(value[()], int):
            env[name] = value[()]
        elif (0, ) in value and isinstance(value[(0, )], int):
            f: Dict[int, int] = {i: a_i for (i, ), a_i in value.items()}  # type: ignore
            env[name] = [f[i] for i in range(max(f.keys()) + 1)]
        elif (0, 0) in value and isinstance(value[(0, 0)], int):
            g: Dict[int, Dict[int, int]] = {}
            for (i, j), a_i_j in value.items():
                if i not in g:
                    g[i] = {}
                g[i][j] = a_i_j  # type: ignore
            env[name] = [[g[i][j] for j in range(max(g[i].keys()) + 1)] for i in range(max(g.keys()) + 1)]
    return env


def _match_format_dfs(node: FormatNode, tokens: List[str], *, variables: Dict[VarName, VarDecl], values: Dict[VarName, Dict[Tuple[int, ...], Union[int, float, str]]]) -> None:
    """
    :raises FormatMatchError:
    """

    if isinstance(node, ItemNode):
        if not tokens:
            raise FormatMatchError('unexpected end of tokens')
        token = tokens.pop()
        if token == '\n':
            raise FormatMatchError('unexpected newline')
        value: Optional[Union[int, float, str]] = None

        # int
        if value is None and (token == '0' or not token.startswith('0')):
            try:
                if int(token) < 2**64:
                    value = int(token)
            except ValueError:
                pass

        # float
        if value is None and '.' in token:
            try:
                value = float(token)
            except ValueError:
                pass

        # str
        if value is None:
            value = token

        # update
        ix = []
        env = _get_env(values)
        for str_i, str_dim, str_base in zip(node.indices, variables[node.name].dims, variables[node.name].bases):
            i = evaluate(Expr(f"""{str_i} - ({str_base})"""), env=env)
            dim = evaluate(str_dim, env=env)
            if i is None:
                raise FormatMatchError(f"""failed to evaluate: {str_i} - ({str_base})""")
            if dim is None:
                raise FormatMatchError(f"""failed to evaluate: {str_dim}""")
            if i < 0 or dim <= i:
                raise FormatMatchError(f"""out of bound: index is {i} but size is {dim}""")
            ix.append(i)
        values[node.name][tuple(ix)] = value

    elif isinstance(node, NewlineNode):
        if not tokens:
            raise FormatMatchError('unexpected end of tokens')
        if tokens[-1] != '\n':
            raise FormatMatchError(f"""unexpected non-newline: {repr(tokens[-1])}""")
        tokens.pop()

    elif isinstance(node, SequenceNode):
        for item in node.items:
            _match_format_dfs(item, tokens, variables=variables, values=values)

    elif isinstance(node, LoopNode):
        size = evaluate(node.size, env=_get_env(values))
        if size is None:
            raise FormatMatchError(f"""failed to evaluate: {node.size}""")
        for i in range(size):
            assert node.name not in values
            values[node.name] = {(): i}
            _match_format_dfs(node.body, tokens, variables=variables, values=values)
            del values[node.name]

    else:
        assert False


def match_format(
    node: FormatNode,
    data: str,
    *,
    variables: Dict[VarName, VarDecl],
    values: Optional[Dict[VarName, Dict[Tuple[int, ...], Union[int, float, str]]]] = None,
) -> Dict[VarName, Dict[Tuple[int, ...], Union[int, float, str]]]:
    """
    :raises FormatMatchError:
    :param values: is an optional argument to specify pre-defined variables.
    """

    # prepare buffer
    if values is None:
        values = {}
    for name in variables.keys():
        assert name not in values
        values[name] = {}

    # tokenize input
    tokens = []
    for line in data.splitlines():
        tokens.extend(line.split())
        tokens.append('\n')
    tokens.reverse()

    # match
    _match_format_dfs(node, tokens, variables=variables, values=values)
    if tokens:
        raise FormatMatchError(f"""end of tokens is expected, but {repr(tokens[0])} found""")
    return values
