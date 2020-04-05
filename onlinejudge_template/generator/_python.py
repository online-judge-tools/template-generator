from typing import *

from onlinejudge_template.types import *


class PythonGeneratorError(GeneratorError):
    pass


class TokenizedInputRequiredError(PythonGeneratorError):
    pass


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
    def __init__(self, exprs: List[Tuple[str, VarDecl]]):
        self.exprs = exprs


class InputNode(PythonNode):
    def __init__(self, exprs: List[Tuple[str, VarDecl]]):
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
