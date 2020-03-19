import itertools
from logging import getLogger
from typing import *

from onlinejudge_template.types import *
from onlinejudge_template.utils import evaluate

logger = getLogger(__name__)


class FormatMatchError(AnalyzerError):
    pass


class TypingError(AnalyzerError):
    pass


def _get_env(values: Dict[str, Dict[Tuple[int, ...], Union[int, float, str]]]) -> Dict[str, int]:
    env: Dict[str, int] = {}
    for name, value in values.items():
        if () in value and isinstance(value[()], int):
            env[name] = value[()]
    return env


def _match_format_dfs(node: FormatNode, tokens: List[str], *, variables: Dict[str, VarDecl], values: Dict[str, Dict[Tuple[int, ...], Union[int, float, str]]]) -> None:
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
        if value is None:
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
            i = evaluate(f"""{str_i} - ({str_base})""", env=env)
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
            values[node.name] = {(): i}
            _match_format_dfs(node.body, tokens, variables=variables, values=values)
        del values[node.name]

    else:
        assert False


def match_format(node: FormatNode, data: str, *, variables: Dict[str, VarDecl]) -> Dict[str, Dict[Tuple[int, ...], Union[int, float, str]]]:
    """
    :raises FormatMatchError:
    """

    # prepare buffer
    values: Dict[str, Dict[Tuple[int, ...], Union[int, float, str]]] = {}
    for name in variables.keys():
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

    # check results
    env = _get_env(values)
    for name, decl in variables.items():
        dims: List[int] = []
        for str_dim in decl.dims:
            dim = evaluate(str_dim, env=env)
            if dim is None:
                raise FormatMatchError(f"""failed to evaluate: {str_dim}""")
            dims.append(dim)
        for ix in itertools.product(*map(lambda n: range(n), dims)):
            if ix not in values[name]:
                raise FormatMatchError(f"""matched, but {name}{ix} is not assigned""")
    return values


def get_var_type(value: Union[int, float, str]) -> VarType:
    if isinstance(value, int):
        return VarType.ValueInt
    elif isinstance(value, float):
        return VarType.Float
    elif isinstance(value, str):
        if len(value) == 1:
            return VarType.Char
        else:
            return VarType.String
    else:
        assert False


def unify_types(t1: VarType, t2: VarType) -> Optional[VarType]:
    if t1 == t2:
        return t1
    if set([t1, t2]) == set([VarType.Char, VarType.String]):
        return VarType.String
    return None


def get_var_types_from_match_result(values: Dict[str, Dict[Tuple[int, ...], Union[int, float, str]]], *, variables: Dict[str, VarDecl]) -> Dict[str, VarType]:
    """
    :raises TypingError:
    """

    types: Dict[str, VarType] = {}
    for name in variables.keys():
        ts = set(map(get_var_type, values[name].values()))
        if len(ts) != 1:
            raise TypingError(f"""failed to infer type: {name} has non-unique candidates {ts}""")
        types[name] = ts.pop()
    for decl in variables.values():
        for name in decl.depending:
            if types[name] not in (VarType.IndexInt, VarType.ValueInt):
                raise TypingError(f"""failed to infer type: {name} used as indices but the type is not an integer""")
            types[name] = VarType.IndexInt
    for name, decl in variables.items():
        if decl.type is not None:
            t = unify_types(types[name], decl.type)
            if t is None:
                raise TypingError(f"""failed to unify types: {types[name]} and {decl.type} for variable {name}""")
            types[name] = t
    return types


def unify_var_types(t1: Dict[str, VarType], t2: Dict[str, VarType]) -> Dict[str, VarType]:
    assert set(t1.keys()) == set(t2.keys())
    t3: Dict[str, VarType] = {}
    for name in t1.keys():
        t = unify_types(t1[name], t2[name])
        if t is None:
            raise TypingError(f"""failed to unify types: {t1[name]} and {t2[name]} for variable {name}""")
        t3[name] = t
    return t3


def infer_types_from_instances(node: FormatNode, *, variables: Dict[str, VarDecl], instances: List[bytes]) -> Dict[str, VarType]:
    """
    :raises FormatMatchError:
    :raises TypingError:
    """

    assert instances
    types: Optional[Dict[str, VarType]] = None
    for data in instances:
        values = match_format(node, data.decode(), variables=variables)
        types2 = get_var_types_from_match_result(values, variables=variables)
        if types is None:
            types = types2
        else:
            types = unify_var_types(types, types2)
    assert types is not None
    return types


def update_variables_with_types(*, variables: Dict[str, VarDecl], types: Dict[str, VarType]) -> Dict[str, VarDecl]:
    updated: Dict[str, VarDecl] = {}
    for name, decl in variables.items():
        if decl.type is None:
            t = types[name]
        else:
            t1 = unify_types(types[name], decl.type)
            if t1 is None:
                raise TypingError(f"""failed to unify types: {types[name]} and {decl.type} for variable {name}""")
            t = t1
        updated[name] = VarDecl(
            type=t,
            name=decl.name,
            dims=decl.dims,
            bases=decl.bases,
            depending=decl.depending,
        )
    return updated
