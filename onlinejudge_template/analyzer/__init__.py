import abc
import pathlib
import sys
from logging import getLogger
from typing import *

import bs4
import ply.lex as lex
import ply.yacc as yacc
import requests
import sympy
import sympy.parsing.sympy_parser as sympy_parser
from onlinejudge_template.types import *

logger = getLogger(__name__)


class TemplateGeneratorError(RuntimeError):
    pass


class HTMLParserError(TemplateGeneratorError):
    pass


class LexerError(TemplateGeneratorError):
    pass


class ParserError(TemplateGeneratorError):
    pass


class SyntaxError(TemplateGeneratorError):
    pass


def get_format_string(url: str, soup: bs4.BeautifulSoup) -> str:
    if 'atcoder.jp' in url:
        for h3 in soup.find_all('h3'):
            if h3.string == '入力':
                s = ''
                for it in h3.parent.find('pre'):
                    s += it.string or it
                return s
        raise HTMLParserError

    elif 'yukicoder.me' in url:
        for h4 in soup.find_all('h4'):
            if h4.string == '入力':
                return h4.parent.find('pre').string
        raise HTMLParserError

    elif 'judge.yosupo.jp' in url:
        for h2 in soup.find_all('h2'):
            if h2.string in ('Input', 'Input / 入力', '入力'):
                return h2.find_next_sibling('pre').string
        raise HTMLParserError

    else:
        raise NotImplementedError


tokens = (
    'NEWLINE',
    # 'SPACE',

    # 'DOLLAR',
    # 'VAR_OPEN',
    # 'VAR_CLOSE',
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
        r"""(\\ |\\,|\\;|~)"""
        return None

    def t_error(t: lex.LexToken) -> None:
        raise LexerError("unexpected character: '{}' at line {} column {}".format(t.value[0], t.lineno, t.lexpos))

    # t_DOLLAR = r'\$'
    # t_VAR_OPEN = r'<\s*[vV][aA][rR]\s*>'
    # t_VAR_CLOSE = r'<\s*/\s*[vV][aA][rR]\s*>'

    t_IDENT = r'[A-Za-z]+'
    t_NUMBER = r'[0-9]+'

    t_UNDERSCORE = r'_'
    t_LBRACE = r'{'
    t_RBRACE = r'}'
    t_COMMA = r','

    t_ADD = r'\+'
    t_SUB = r'-'
    t_MUL = r'(\*|x|×|\\times)'
    t_DIV = r'/'

    t_DOTS = r'(\.\.\.*|…|\\dots|\\ldots)'
    t_VDOTS = r'(:|⋮|\\vdots)'

    return lex.lex()


class ParserNode(abc.ABC):
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
                 | item items
                 | item"""
        if len(p) == 5:
            dots = DotsParserNode(first=p[1], last=p[3], **loc(p))
            p[0] = SequenceParserNode(items=[dots] + p[2].items, **loc(p))
        elif len(p) == 3:
            p[0] = SequenceParserNode(items=[p[1]] + p[2].items, **loc(p))
        elif len(p) == 2:
            p[0] = SequenceParserNode(items=[p[1]], **loc(p))

    def p_item(p: yacc.YaccProduction) -> None:
        """item : IDENT
                | IDENT UNDERSCORE NUMBER
                | IDENT UNDERSCORE IDENT
                | IDENT UNDERSCORE LBRACE RBRACE"""
        if len(p) == 2:
            p[0] = ItemParserNode(name=p[1], indices=(), **loc(p))
        elif len(p) == 4:
            p[0] = ItemParserNode(name=p[1], indices=(p[3], ), **loc(p))
        elif len(p) == 5:
            raise NotImplementedError

    def p_error(t: lex.LexToken) -> None:
        raise ParserError("unexpected token: {} \"{}\" at line {} column {}".format(t.type, t.value, t.lineno, find_column(t.lexpos)))

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


def simplify(s: str) -> sympy.Expr:
    transformations = sympy_parser.standard_transformations + (sympy_parser.implicit_multiplication_application, )
    local_dict = {'N': sympy.Symbol('N')}
    return sympy_parser.parse_expr(s, local_dict=local_dict, transformations=transformations)


def zip_nodes(a: FormatNode, b: FormatNode, *, name: str, first: Optional[str], last: Optional[str]) -> Tuple[FormatNode, Optional[str], Optional[str]]:
    if isinstance(a, ItemNode) and isinstance(b, ItemNode):
        if a.name != b.name or len(a.indices) != len(b.indices):
            raise SyntaxError("unmatched dots pair: {} and {}".format(a, b))
        indices = []
        for i, j in zip(a.indices, b.indices):
            if simplify(i) == simplify(j):
                indices.append(i)
            else:
                if first is None and last is None:
                    first = i
                    last = j
                else:
                    if not simplify(f"{j} - {i}") != simplify(f"{first} - {last}"):
                        raise SyntaxError("unmatched dots pair: {} and {}".format(a, b))
                indices.append(str(simplify(f"{i} - {first} + {name}")))
        return ItemNode(name=a.name, indices=indices), first, last

    elif isinstance(a, NewlineNode) and isinstance(b, NewlineNode):
        return NewlineNode(), first, last

    elif isinstance(a, SequenceNode) and isinstance(b, SequenceNode):
        if len(a.items) != len(b.items):
            raise SyntaxError("unmatched dots pair: {} and {}".format(a, b))
        items = []
        for a_i, b_i in zip(a.items, b.items):
            c_i, first, last = zip_nodes(a_i, b_i, name=name, first=first, last=last)
            items.append(c_i)
        return SequenceNode(items=items), first, last

    elif isinstance(a, LoopNode) and isinstance(b, LoopNode):
        if a.size != b.size or a.name != b.name:
            raise SyntaxError("unmatched dots pair: {} and {}".format(a, b))
        c, first, last = zip_nodes(a.body, b.body, name=name, first=first, last=last)
        return LoopNode(size=a.size, name=a.name, body=c), first, last

    else:
        raise SyntaxError("unmatched dots pair: {} and {}".format(a, b))


def analyze(node: ParserNode) -> FormatNode:
    if isinstance(node, ItemParserNode):
        indices = [str(simplify(index)) for index in node.indices]
        return ItemNode(name=node.name, indices=indices)

    elif isinstance(node, NewlineParserNode):
        return NewlineNode()

    elif isinstance(node, SequenceParserNode):
        items = []
        for item in map(analyze, node.items):
            if isinstance(item, SequenceNode):
                items.extend(item.items)
            else:
                items.append(item)
        return SequenceNode(items=items)

    elif isinstance(node, DotsParserNode):
        a = analyze(node.first)
        b = analyze(node.last)

        # find the name of the new loop counter
        used_names = list_used_names(a) | list_used_names(b)
        name = 'i'
        while name in used_names:
            assert name != 'z'
            name = chr(ord(name) + 1)

        # zip bodies
        c, first, last = zip_nodes(a, b, name=name, first=None, last=None)
        size = str(simplify(f"{last} - {first} + 1"))
        return LoopNode(size=size, name=name, body=c)

    else:
        assert False


def download_html(url: str) -> bs4.BeautifulSoup:
    # get HTML
    resp = requests.get(url)
    logger.debug('HTTP response: %s', resp)
    resp.raise_for_status()

    # parse HTML
    soup = bs4.BeautifulSoup(resp.content.decode(resp.encoding), 'html.parser')
    logger.debug('parsed HTML: %s...', repr(str(soup))[:200])

    return soup


def run(soup: bs4.BeautifulSoup, *, url: str) -> FormatNode:
    # find the format <pre> tag
    pre = get_format_string(url, soup)
    pre = pre.rstrip() + '\n'
    logger.debug('format string: %s', repr(pre))

    # list tokens with lex
    lexer = build_lexer()
    lexer.input(pre)
    logger.debug('Lex tokens: %s', list(lexer.clone()))

    # make a tree with yacc
    parser = build_parser(input=pre)
    parsed = parser.parse(lexer=lexer)
    logger.debug('Yacc tree: %s', parsed)

    # analyze the syntax tree
    ast = analyze(parsed)
    logger.debug('abstract syntax tree: %s', ast)

    return ast
