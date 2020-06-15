import abc
import enum
from typing import *


class FormatNode(abc.ABC):
    """
    .. note::
       仕様はこれでよさそうな感じある？
    """
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
    """
    .. todo::
       `name` を `counter` とかに rename する？
    """

    size: str
    name: str
    body: FormatNode

    def __init__(self, *, size: str, name: str, body: FormatNode):
        self.size = size
        self.name = name
        self.body = body


class SampleCase(NamedTuple):
    input: bytes
    output: bytes


class AnalyzerResources(NamedTuple):
    url: Optional[str]
    html: Optional[bytes]

    input_format_string: Optional[str]
    output_format_string: Optional[str]
    sample_cases: Optional[List[SampleCase]]


class VarType(enum.Enum):
    """
    .. todo::
       仕様の確定
    """

    IndexInt = 'IndexInt'
    ValueInt = 'ValueInt'
    Float = 'Float'
    String = 'String'
    Char = 'Char'
    # NegativeOne = 'NegativeOne'


class VarDecl(NamedTuple):
    """
    .. todo::
       仕様の確定
    """

    name: str
    type: Optional[VarType]
    dims: List[str]
    bases: List[str]
    depending: Set[str]


class ConstantDecl(NamedTuple):
    """
    .. todo::
       仕様の確定
    """

    name: str
    value: str
    type: VarType


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


class TopcoderType(enum.Enum):
    Int = 'int'
    Long = 'long'
    Double = 'double'
    String = 'String'
    IntList = 'int[]'
    LongList = 'long[]'
    DoubleList = 'double[]'
    StringList = 'String[]'


class TopcoderClassDefinition(NamedTuple):
    class_name: str
    method_name: str
    formal_arguments: List[Tuple[TopcoderType, str]]
    return_type: TopcoderType


class AnalyzerResult(NamedTuple):
    """
    .. todo::
       仕様の確定
    """

    resources: AnalyzerResources
    input_format: Optional[FormatNode]
    input_variables: Optional[Dict[str, VarDecl]]
    output_format: Optional[FormatNode]
    output_variables: Optional[Dict[str, VarDecl]]
    constants: Dict[str, ConstantDecl]
    output_type: Optional[OutputType]
    topcoder_class_definition: Optional[TopcoderClassDefinition]


class TemplateAnalyzerGeneratorError(RuntimeError):
    pass


class AnalyzerError(TemplateAnalyzerGeneratorError):
    pass


class GeneratorError(TemplateAnalyzerGeneratorError):
    pass
