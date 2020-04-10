import abc
from typing import *

from onlinejudge_template.types import *


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


class GenerateNode(CPlusPlusNode):
    def __init__(self, expr: Tuple[str, Optional[VarType]]):
        self.expr = expr


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
