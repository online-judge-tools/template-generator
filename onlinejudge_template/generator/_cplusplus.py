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
