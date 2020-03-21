"""
the module to parse format strings and construct format trees

この module はフォーマット文字列を構文解析しフォーマット木を作ります。
たとえば
::

    N
    P_0 P_1 \cdots P_{N-1}
    Q_0 Q_1 \cdots Q_{N-1}

という入力フォーマット文字列が与えられれば
::

    sequence([
        item("N"),
        newline(),
        loop(counter="i", size="N",
            item("P", indices="i")
        ),
        newline(),
        loop(counter="i", size="N",
            item("Q", indices="i")
        ),
        newline(),
    ])

に相当する木構造 (:any:`FormatNode`) を返します。
"""

import abc
import re
from logging import getLogger
from typing import *

import ply.lex as lex
import ply.yacc as yacc
from onlinejudge_template.types import *
from onlinejudge_template.utils import simplify

logger = getLogger(__name__)


class FormatStringParserError(AnalyzerError):
    pass


tokens = (
    'NEWLINE',
    # 'SPACE',

    # 'DOLLAR',
    # 'VAR_OPEN',
    # 'VAR_CLOSE',
    'FONTSPEC',
    'IDENT',
    'NUMBER',
    'UNDERSCORE',
    'LBRACE',
    'RBRACE',
    'COMMA',
    'ADD',
    'SUB',
    'MUL',
    'DIV',
    'VDOTS',
    'DOTS',
)


def build_lexer() -> lex.Lexer:
    def t_NEWLINE(t: lex.LexToken) -> lex.LexToken:
        r"""\r?\n"""
        t.lexer.lineno += 1
        return t

    t_ignore = ' \t$'

    def t_tex_space(t: lex.LexToken) -> None:
        r"""(\\[ ]|\\,|\\;|~)"""
        return None

    def t_error(t: lex.LexToken) -> None:
        raise FormatStringParserError("lexer: unexpected character: '{}' at line {} column {}".format(t.value[0], t.lineno, t.lexpos))

    # t_DOLLAR = r'\$'
    # t_VAR_OPEN = r'<\s*[vV][aA][rR]\s*>'
    # t_VAR_CLOSE = r'<\s*/\s*[vV][aA][rR]\s*>'

    def t_FONTSPEC(t: lex.LexToken) -> lex.LexToken:
        r"""\\(rm|mathrm|mathtt|mathbf|mathit|mathscr|mathcal|mathfrak|mathbb)"""
        return t

    t_IDENT = r'[A-Za-z]+'
    t_NUMBER = r'[0-9]+'

    t_UNDERSCORE = r'_'
    t_LBRACE = r'{'
    t_RBRACE = r'}'
    t_COMMA = r','

    t_ADD = r'\+'
    t_SUB = r'-'
    t_MUL = r'(\*|×|\\times)'
    t_DIV = r'/'

    t_DOTS = r'(\.\.\.*|…|\\dots|\\ldots|\\cdots)'
    t_VDOTS = r'(:|⋮|\\vdots)'

    return lex.lex()


class ParserNode(abc.ABC):
    """
    an internal representation which Yacc generates
    """

    line: int
    column: int

    def __init__(self, *, line: int, column: int):
        self.line = line
        self.column = column

    def __repr__(self) -> str:
        keys = dir(self)
        keys = list(filter(lambda key: not key.startswith('_'), keys))
        keys.sort()
        keys.remove('line')
        keys.remove('column')
        keys.append('line')
        keys.append('column')
        items = ', '.join([key + '=' + repr(getattr(self, key)) for key in keys])
        return f"{self.__class__.__name__}({items})"


class SequenceParserNode(ParserNode):
    items: List[ParserNode]

    def __init__(self, *, items: List[ParserNode], line: int, column: int):
        super().__init__(line=line, column=column)
        self.items = items


class NewlineParserNode(ParserNode):
    pass


class ItemParserNode(ParserNode):
    name: str
    indices: Union[Tuple[str], Tuple]

    def __init__(self, *, name: str, indices: Union[Tuple[str], Tuple] = (), line: int, column: int):
        super().__init__(line=line, column=column)
        self.name = name
        self.indices = indices


class DotsParserNode(ParserNode):
    first: ParserNode
    last: ParserNode

    def __init__(self, *, first: ParserNode, last: ParserNode, line: int, column: int):
        super().__init__(line=line, column=column)
        self.first = first
        self.last = last


def build_parser(*, input: str) -> yacc.LRParser:
    def find_column(lexpos: int) -> int:
        line_start = input.rfind('\n', 0, lexpos) + 1
        return lexpos - line_start + 1

    def loc(p: yacc.YaccProduction) -> Dict[str, int]:
        return {
            'line': p.lineno(1),
            'column': find_column(p.lexpos(1)),
        }

    def p_main(p: yacc.YaccProduction) -> None:
        """main : lines main
                | lines"""
        if len(p) == 3:
            p[0] = SequenceParserNode(items=[p[1]] + p[2].items, **loc(p))
        elif len(p) == 2:
            p[0] = SequenceParserNode(items=[p[1]], **loc(p))

    def p_lines(p: yacc.YaccProduction) -> None:
        """lines : line
                 | line VDOTS newline line
                 | line DOTS newline line"""
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 5:
            p[0] = DotsParserNode(first=p[1], last=p[4], **loc(p))

    def p_newline(p: yacc.YaccProduction) -> None:
        """newline : NEWLINE"""
        p[0] = NewlineParserNode(**loc(p))

    def p_line(p: yacc.YaccProduction) -> None:
        """line : items newline"""
        p[0] = SequenceParserNode(items=p[1].items + [p[2]], **loc(p))

    def p_items(p: yacc.YaccProduction) -> None:
        """items : item DOTS item items
                 | item DOTS item
                 | item items
                 | item"""
        if len(p) == 5:
            dots = DotsParserNode(first=p[1], last=p[3], **loc(p))
            p[0] = SequenceParserNode(items=[dots] + p[2].items, **loc(p))
        if len(p) == 4:
            dots = DotsParserNode(first=p[1], last=p[3], **loc(p))
            p[0] = SequenceParserNode(items=[dots], **loc(p))
        elif len(p) == 3:
            p[0] = SequenceParserNode(items=[p[1]] + p[2].items, **loc(p))
        elif len(p) == 2:
            p[0] = SequenceParserNode(items=[p[1]], **loc(p))

    def p_item(p: yacc.YaccProduction) -> None:
        """item : IDENT
                | IDENT UNDERSCORE NUMBER
                | IDENT UNDERSCORE IDENT
                | IDENT UNDERSCORE LBRACE exprs RBRACE
                | FONTSPEC LBRACE item RBRACE
                | LBRACE FONTSPEC item RBRACE"""
        if len(p) == 2:
            p[0] = ItemParserNode(name=p[1], indices=(), **loc(p))
        elif len(p) == 4:
            p[0] = ItemParserNode(name=p[1], indices=(p[3], ), **loc(p))
        elif len(p) == 6:
            p[0] = ItemParserNode(name=p[1], indices=p[4], **loc(p))
        elif len(p) == 5:
            p[0] = p[3]

    def p_exprs(p: yacc.YaccProduction) -> None:
        """exprs : expr COMMA exprs
                 | expr"""
        if len(p) == 3:
            p[0] = (p[1], *p[2])
        elif len(p) == 2:
            p[0] = (p[1], )

    def p_expr(p: yacc.YaccProduction) -> None:
        """expr : IDENT
                | NUMBER
                | NUMBER IDENT
                | IDENT binop expr
                | NUMBER binop expr"""
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 3:
            p[0] = f"""{p[1]} * {p[2]}"""
        elif len(p) == 4:
            p[0] = f"""{p[1]} {p[2]} {p[3]}"""

    def p_binop(p: yacc.YaccProduction) -> None:
        """binop : ADD
                 | SUB
                 | MUL
                 | DIV"""
        p[0] = p[1]

    def p_error(t: lex.LexToken) -> None:
        raise FormatStringParserError("parser: unexpected token: {} \"{}\" at line {} column {}".format(t.type, t.value, t.lineno, find_column(t.lexpos)))

    return yacc.yacc(debug=False, write_tables=False)


def list_used_names(node: FormatNode) -> Set[str]:
    if isinstance(node, ItemNode):
        return set([node.name])

    elif isinstance(node, NewlineNode):
        return set()

    elif isinstance(node, SequenceNode):
        names: Set[str] = set()
        for item in node.items:
            names |= list_used_names(item)
        return names

    elif isinstance(node, LoopNode):
        return set([node.name]) | list_used_names(node.body)

    else:
        assert False


def zip_nodes(a: FormatNode, b: FormatNode, *, name: str, size: Optional[str]) -> Tuple[FormatNode, Optional[str]]:
    """
    :raises FormatStringParserError:
    """

    if isinstance(a, ItemNode) and isinstance(b, ItemNode):
        if a.name != b.name or len(a.indices) != len(b.indices):
            raise FormatStringParserError("semantics: unmatched dots pair: {} and {}".format(a, b))
        indices = []
        for i, j in zip(a.indices, b.indices):
            if simplify(i) == simplify(j):
                indices.append(i)
            else:
                if size is None:
                    size = simplify(f"""{j} - {i} + 1""")
                else:
                    if simplify(f"""{j} - {i} + 1""") != simplify(size):
                        raise FormatStringParserError("semantics: unmatched dots pair: {} and {}".format(a, b))
                indices.append(simplify(f"{i} + {name}"))
        return ItemNode(name=a.name, indices=indices), size

    elif isinstance(a, NewlineNode) and isinstance(b, NewlineNode):
        return NewlineNode(), size

    elif isinstance(a, SequenceNode) and isinstance(b, SequenceNode):
        if len(a.items) != len(b.items):
            raise FormatStringParserError("semantics: unmatched dots pair: {} and {}".format(a, b))
        items = []
        for a_i, b_i in zip(a.items, b.items):
            c_i, size = zip_nodes(a_i, b_i, name=name, size=size)
            items.append(c_i)
        return SequenceNode(items=items), size

    elif isinstance(a, LoopNode) and isinstance(b, LoopNode):
        if a.size != b.size or a.name != b.name:
            raise FormatStringParserError("semantics: unmatched dots pair: {} and {}".format(a, b))
        c, size = zip_nodes(a.body, b.body, name=name, size=size)
        return LoopNode(size=a.size, name=a.name, body=c), size

    else:
        raise FormatStringParserError("semantics: unmatched dots pair: {} and {}".format(a, b))


def exnted_loop_node(a: FormatNode, b: FormatNode, *, loop: LoopNode) -> Optional[FormatNode]:
    if isinstance(a, ItemNode) and isinstance(b, ItemNode):
        if a.name != b.name or len(a.indices) != len(b.indices):
            return None
        indices = []
        for i, j in zip(a.indices, b.indices):
            decr_j, _ = re.subn(r'\b' + re.escape(loop.name) + r'\b', '(-1)', j)
            if simplify(i) == simplify(decr_j):
                indices.append(simplify(f"""{i} + {loop.name}"""))
            else:
                return None
        return ItemNode(name=a.name, indices=indices)

    elif isinstance(a, NewlineNode) and isinstance(b, NewlineNode):
        return NewlineNode()

    elif isinstance(a, SequenceNode) and isinstance(b, SequenceNode):
        if len(a.items) != len(b.items):
            return None
        items = []
        for a_i, b_i in zip(a.items, b.items):
            c_i = exnted_loop_node(a_i, b_i, loop=loop)
            if c_i is None:
                return None
            items.append(c_i)
        return SequenceNode(items=items)

    elif isinstance(a, LoopNode) and isinstance(b, LoopNode):
        if a.size != b.size or a.name != b.name:
            return None
        c = exnted_loop_node(a.body, b.body, loop=loop)
        if c is None:
            return None
        return LoopNode(size=a.size, name=a.name, body=c)

    else:
        return None


def analyze_parsed_node(node: ParserNode) -> FormatNode:
    """
    translates an internal representation :any:`ParserNode` to a result tree :any:`FormatNode`

    :raises FormatStringParserError:
    """

    if isinstance(node, ItemParserNode):
        indices = [simplify(index) for index in node.indices]
        return ItemNode(name=node.name, indices=indices)

    elif isinstance(node, NewlineParserNode):
        return NewlineNode()

    elif isinstance(node, SequenceParserNode):
        items: List[FormatNode] = []
        que: List[FormatNode] = list(map(analyze_parsed_node, node.items))
        while que:
            item, *que = que
            if isinstance(item, SequenceNode):
                # flatten SequenceNode in SequenceNode
                que = item.items + que
            elif isinstance(item, LoopNode) and items:
                # merge FormatNode with LoopNode if possible
                if isinstance(item.body, SequenceNode) and len(items) >= len(item.body.items):
                    items_init = items[:-len(item.body.items)]
                    items_tail: FormatNode = SequenceNode(items=items[-len(item.body.items):])
                else:
                    items_init = items[:-1]
                    items_tail = items[-1]
                extended_body = exnted_loop_node(items_tail, item.body, loop=item)
                if extended_body is not None:
                    extended_loop: FormatNode = LoopNode(size=simplify(f"""{item.size} + 1"""), name=item.name, body=extended_body)
                    items = items_init
                    que = [extended_loop] + que
                else:
                    items.append(item)
            else:
                items.append(item)
        if len(items) == 1:
            # return the node directly if the length is 1
            return items[0]
        else:
            return SequenceNode(items=items)

    elif isinstance(node, DotsParserNode):
        a = analyze_parsed_node(node.first)
        b = analyze_parsed_node(node.last)

        # find the name of the new loop counter
        used_names = list_used_names(a) | list_used_names(b)
        name = 'i'
        while name in used_names:
            assert name != 'z'
            name = chr(ord(name) + 1)

        # zip bodies
        c, size = zip_nodes(a, b, name=name, size=None)
        if size is None:
            raise FormatStringParserError("semantics: unmatched dots pair: {} and {}".format(a, b))
        return LoopNode(size=size, name=name, body=c)

    else:
        assert False


def run(pre: str) -> FormatNode:
    """
    :raises FormatStringParserError:
    """

    # list tokens with lex
    lexer = build_lexer()
    lexer.input(pre)
    logger.debug('Lex tokens: %s', list(lexer.clone()))

    # make a tree with yacc
    parser = build_parser(input=pre)
    parsed = parser.parse(lexer=lexer)
    logger.debug('Yacc tree: %s', parsed)

    # analyze the syntax tree
    ast = analyze_parsed_node(parsed)
    logger.debug('abstract syntax tree: %s', ast)

    return ast
