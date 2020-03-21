"""
the module to infer types of variables in format trees

この module はフォーマット木の中に自由に出現する変数の型を推論します。
サンプル文字列とのマッチ結果を解析することで実装されています。

たとえば
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N", sequence([
            item("A", indices="i"),
            newline(),
        )),
    ])

のようなフォーマット木 (:any:`FormatNode`) と
::

    3
    ABA
    AAABA
    BAAB

というサンプル文字列が与えられれば
::

    {
        "N": int,
        "A": str,
    }

に相当する結果を返します。
"""

from logging import getLogger
from typing import *

from onlinejudge_template.analyzer.match import match_format
from onlinejudge_template.types import *

logger = getLogger(__name__)


class TypingError(AnalyzerError):
    pass


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
        while len(ts) >= 2:
            t1 = ts.pop()
            t2 = ts.pop()
            t3 = unify_types(t1, t2)
            if t3 is None:
                raise TypingError(f"""failed to unify types: {t1} and {t2} for variable {name}""")
            ts.add(t3)
        if not ts:
            raise TypingError(f"""failed to infer type: {name} has no candidate types""")
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
    for i, data in enumerate(instances):
        values = match_format(node, data.decode(), variables=variables)
        logger.debug("match result for %d-th data: %s", i, values)
        types2 = get_var_types_from_match_result(values, variables=variables)
        if types is None:
            types = types2
        else:
            types = unify_var_types(types, types2)
    assert types is not None
    logger.debug("infered types: %s", types)
    return types


def update_variables_with_types(*, variables: Dict[str, VarDecl], types: Dict[str, VarType]) -> Dict[str, VarDecl]:
    """
    :raises TypingError:
    """

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
