import abc
import enum
from typing import *

VarName = NewType('VarName', str)  # A name of variable. Its type is int, sequence of int, etc.. For example, "a", "b", "f", and "ans" are VarName. However, "a_i" is not a VarName.
Expr = NewType('Expr', str)  # An expr. The type is always int. For example, "n + 1", "a_i", "x", and "2 * x" are Expr.


class FormatNode(abc.ABC):
    def __repr__(self) -> str:
        keys = dir(self)
        keys = list(filter(lambda key: not key.startswith('_'), keys))
        keys.sort()
        items = ', '.join([key + '=' + repr(getattr(self, key)) for key in keys])
        return f"{self.__class__.__name__}({items})"


class ItemNode(FormatNode):
    name: VarName
    indices: List[Expr]

    def __init__(self, *, name: str, indices: Sequence[str] = []):
        self.name = VarName(name)
        self.indices = list(map(Expr, indices))


class NewlineNode(FormatNode):
    pass


class SequenceNode(FormatNode):
    items: List[FormatNode]

    def __init__(self, *, items: Sequence[FormatNode]):
        self.items = list(items)


class LoopNode(FormatNode):
    size: Expr
    name: VarName  # TODO: rename `name` with `counter`
    body: FormatNode

    def __init__(self, *, size: str, name: str, body: FormatNode):
        self.size = Expr(size)
        self.name = VarName(name)
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
    IndexInt = 'IndexInt'
    ValueInt = 'ValueInt'
    Float = 'Float'
    String = 'String'
    Char = 'Char'
    # NegativeOne = 'NegativeOne'


class VarDecl(NamedTuple):
    name: VarName
    type: Optional[VarType]
    dims: List[Expr]
    bases: List[Expr]
    depending: Set[VarName]


class ConstantDecl(NamedTuple):
    name: VarName
    value: str  # For example, "1000000007", "Yes", "No". Not Expr type.
    type: VarType


class OutputType(abc.ABC):
    pass


class YesNoOutputType(OutputType):
    name: Expr
    yes: str
    no: str

    def __init__(self, *, name: Expr, yes: str, no: str):
        self.name = name
        self.yes = yes
        self.no = no


class OneOutputType(OutputType):
    name: Expr
    type: VarType

    def __init__(self, *, name: Expr, type: VarType):
        self.name = name
        self.type = type


class TwoOutputType(OutputType):
    name1: Expr
    type1: VarType
    name2: Expr
    type2: VarType
    print_newline_after_item: bool

    def __init__(self, *, name1: Expr, type1: VarType, name2: Expr, type2: VarType, print_newline_after_item: bool):
        self.name1 = name1
        self.type1 = type1
        self.name2 = name2
        self.type2 = type2
        self.print_newline_after_item = print_newline_after_item


class VectorOutputType(OutputType):
    name: VarName  # This has VarName type instead of Expr type becuase it will be subscripted.
    type: VarType
    subscripted_name: str  # TODO: remove this variable. This has a string like "a[i]", but carrying source code is not responsibility of this class.
    counter_name: VarName
    print_size: bool
    print_newline_after_size: bool
    print_newline_after_item: bool

    def __init__(self, *, name: VarName, type: VarType, subscripted_name: str, counter_name: VarName, print_size: bool, print_newline_after_size: bool, print_newline_after_item: bool):
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
    formal_arguments: List[Tuple[TopcoderType, VarName]]
    return_type: TopcoderType


class AnalyzerResult(NamedTuple):
    resources: AnalyzerResources
    input_format: Optional[FormatNode]
    input_variables: Optional[Dict[VarName, VarDecl]]
    output_format: Optional[FormatNode]
    output_variables: Optional[Dict[VarName, VarDecl]]
    constants: Dict[VarName, ConstantDecl]
    output_type: Optional[OutputType]
    topcoder_class_definition: Optional[TopcoderClassDefinition]


class TemplateAnalyzerGeneratorError(RuntimeError):
    pass


class AnalyzerError(TemplateAnalyzerGeneratorError):
    pass


class GeneratorError(TemplateAnalyzerGeneratorError):
    pass
