"""
the module to analyze output types

この module は出力形式のパターンを分析し簡単化します。

たとえば
::

    N
    A_1 A_2 ... A_N

のような出力フォーマットの場合、戻り値を `std::pair<int, std::vector<int> >` とするのでなく、戻り値を `std::vector<int>` のみとし `int N = A.size();` として `N` を復元するようにした方が便利です。この module このような最適化を目的としています。
"""

from typing import *

from onlinejudge_template.types import *
from onlinejudge_template.utils import simplify


# TODO: remove this
def _get_variable(*, decl: VarDecl, indices: List[str], decls: Dict[str, VarDecl]) -> str:
    var = decl.name
    for index, base in zip(indices, decl.bases):
        i = simplify(f"""{index} - ({base})""", env=set(decls.keys()))
        var = f"""{var}[{i}]"""
    return var


def analyze_output_type(*, output_format: FormatNode, output_variables: Dict[str, VarDecl], constants: Dict[str, ConstantDecl]) -> Optional[OutputType]:
    node = output_format
    decls = output_variables

    # pattern:
    #     ans
    if isinstance(node, SequenceNode) and len(node.items) == 2:
        item0 = node.items[0]
        item1 = node.items[1]
        if isinstance(item0, ItemNode) and isinstance(item1, NewlineNode):
            type = decls[item0.name].type
            if type is not None:
                if 'YES' in constants and 'NO' in constants and type == VarType.String:
                    return YesNoOutputType(name='ans', yes='YES', no='NO')
                if 'FIRST' in constants and 'SECOND' in constants and type == VarType.String:
                    return YesNoOutputType(name='ans', yes='FIRST', no='SECOND')
                return OneOutputType(name='ans', type=type)

    # pattern:
    #     x y
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

    # pattern:
    #     x
    #     y
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

    # pattern:
    #     n
    #     a_1 ... a_n
    if isinstance(node, SequenceNode) and len(node.items) == 4:
        item0 = node.items[0]
        item1 = node.items[1]
        item2 = node.items[2]
        item3 = node.items[3]
        if isinstance(item0, ItemNode) and isinstance(item1, NewlineNode) and isinstance(item3, NewlineNode):
            if isinstance(item2, LoopNode) and isinstance(item2.body, ItemNode) and item2.size == item0.name and item2.body.indices == [item2.name]:
                type = decls[item2.body.name].type
                subscripted_name = _get_variable(decl=decls[item2.body.name], indices=item2.body.indices, decls=decls)
                counter_name = item2.name
                if type is not None:
                    return VectorOutputType(name='ans', type=type, subscripted_name=subscripted_name, counter_name=counter_name, print_size=True, print_newline_after_size=True, print_newline_after_item=False)

    # pattern:
    #     n a_1 ... a_n
    if isinstance(node, SequenceNode) and len(node.items) == 3:
        item0 = node.items[0]
        item1 = node.items[1]
        item2 = node.items[2]
        if isinstance(item0, ItemNode) and isinstance(item2, NewlineNode):
            if isinstance(item1, LoopNode) and isinstance(item1.body, ItemNode) and item1.size == item0.name and item1.body.indices == [item1.name]:
                type = decls[item1.body.name].type
                subscripted_name = _get_variable(decl=decls[item1.body.name], indices=item1.body.indices, decls=decls)
                counter_name = item1.name
                if type is not None:
                    return VectorOutputType(name='ans', type=type, subscripted_name=subscripted_name, counter_name=counter_name, print_size=True, print_newline_after_size=False, print_newline_after_item=False)

    # pattern:
    #     n
    #     a_1
    #     ...
    #     a_n
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
                    subscripted_name = _get_variable(decl=decls[item3.name], indices=item3.indices, decls=decls)
                    counter_name = item2.name
                    if type is not None:
                        return VectorOutputType(name='ans', type=type, subscripted_name=subscripted_name, counter_name=counter_name, print_size=True, print_newline_after_size=True, print_newline_after_item=True)

    return None
