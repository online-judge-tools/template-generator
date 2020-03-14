import abc
from typing import *


class FormatNode(abc.ABC):
    def __repr__(self) -> str:
        keys = dir(self)
        keys = list(filter(lambda key: not key.startswith('_'), keys))
        keys.sort()
        items = ', '.join([key + '=' + repr(getattr(self, key)) for key in keys])
        return f"{self.__class__.__name__}({items})"


class ItemNode(FormatNode):
    name: str
    indices: List[str]

    def __init__(self, *, name: str, indices: Sequence[str] = []):
        self.name = name
        self.indices = list(indices)


class NewlineNode(FormatNode):
    pass


class SequenceNode(FormatNode):
    items: List[FormatNode]

    def __init__(self, *, items: Sequence[FormatNode]):
        self.items = list(items)


class LoopNode(FormatNode):
    size: str
    name: str
    body: FormatNode

    def __init__(self, *, size: str, name: str, body: FormatNode):
        self.size = size
        self.name = name
        self.body = body
