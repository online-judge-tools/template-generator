import argparse
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import bs4
import ply.lex as lex
import ply.yacc as yacc
import requests

logger = getLogger(__name__)


def get_format_string(url: str, soup: bs4.BeautifulSoup) -> str:
    if 'atcoder.jp' in url:
        for h3 in soup.find_all('h3'):
            if h3.string == '入力':
                s = ''
                for it in h3.parent.find('pre'):
                    s += it.string or it
                return s
        raise RuntimeError

    elif 'yukicoder.me' in url:
        for h4 in soup.find_all('h4'):
            if h4.string == '入力':
                return h4.parent.find('pre').string
        raise RuntimeError

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

    def t_error(t: lex.LexToken) -> None:
        raise RuntimeError("unexpected character: '{}' at line {} column {}".format(t.value, t.lineno, t.lexpos))

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


class FormatNode(object):
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


class SequenceNode(FormatNode):
    items: List[FormatNode]

    def __init__(self, *, items: List[FormatNode], line: int, column: int):
        super().__init__(line=line, column=column)
        self.items = items


class NewlineNode(FormatNode):
    pass


class ItemNode(FormatNode):
    name: str
    indices: Union[Tuple[str], Tuple]

    def __init__(self, *, name: str, indices: Union[Tuple[str], Tuple] = (), line: int, column: int):
        super().__init__(line=line, column=column)
        self.name = name
        self.indices = indices


class DotsNode(FormatNode):
    first: FormatNode
    last: FormatNode

    def __init__(self, *, first: FormatNode, last: FormatNode, line: int, column: int):
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
            p[0] = SequenceNode(items=[p[1]] + p[2].items, **loc(p))
        elif len(p) == 2:
            p[0] = SequenceNode(items=[p[1]], **loc(p))

    def p_lines(p: yacc.YaccProduction) -> None:
        """lines : line
                 | line VDOTS newline line
                 | line DOTS newline line"""
        if len(p) == 2:
            p[0] = p[1]
        elif len(p) == 5:
            p[0] = DotsNode(first=p[1], last=p[4], **loc(p))

    def p_newline(p: yacc.YaccProduction) -> None:
        """newline : NEWLINE"""
        p[0] = NewlineNode(**loc(p))

    def p_line(p: yacc.YaccProduction) -> None:
        """line : items newline"""
        p[0] = SequenceNode(items=p[1].items + [p[2]], **loc(p))

    def p_items(p: yacc.YaccProduction) -> None:
        """items : item DOTS item items
                 | item items
                 | item"""
        if len(p) == 5:
            dots = DotsNode(first=p[1], last=p[3], **loc(p))
            p[0] = SequenceNode(items=[dots] + p[2].items, **loc(p))
        elif len(p) == 3:
            p[0] = SequenceNode(items=[p[1]] + p[2].items, **loc(p))
        elif len(p) == 2:
            p[0] = SequenceNode(items=[p[1]], **loc(p))

    def p_item(p: yacc.YaccProduction) -> None:
        """item : IDENT
                | IDENT UNDERSCORE NUMBER
                | IDENT UNDERSCORE IDENT
                | IDENT UNDERSCORE LBRACE RBRACE"""
        if len(p) == 2:
            p[0] = ItemNode(name=p[1], indices=(), **loc(p))
        elif len(p) == 4:
            p[0] = ItemNode(name=p[1], indices=(p[3], ), **loc(p))
        elif len(p) == 5:
            raise NotImplementedError

    def p_error(t: lex.LexToken) -> None:
        raise RuntimeError("unexpected token: {} \"{}\" at line {} column {}".format(t.type, t.value, t.lineno, find_column(t.lexpos)))

    return yacc.yacc(debug=False, write_tables=False)


def run(url: str) -> None:
    # get HTML
    resp = requests.get(url)
    logger.debug('HTTP response: %s', resp)
    resp.raise_for_status()

    # parse HTML
    soup = bs4.BeautifulSoup(resp.content.decode(resp.encoding), 'html.parser')
    logger.debug('parsed HTML: %s...', repr(str(soup))[:200])

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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)
    run(args.url)


if __name__ == '__main__':
    main()
