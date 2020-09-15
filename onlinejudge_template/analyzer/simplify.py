"""
the module to manipulate mathematical expressions (e.g. ``2 * n + 1``, ``a_i + i``)

この module は数式を簡約します。
たとえば ``(n + 1) + (n - 1)`` という式が与えられれば ``2 * n`` という式に簡約して返します。
これは選言標準形のようなものを構成して並べ替えることによって実装されています。

中心部分では、次のような競技プログラミングの問題を解いています:
::
    変数 x, y, z および整数と四則演算と括弧からなる数式が与えられます。
    この数式と等しい数式であって $\sum k_i x^{a_i} y^{b_i} z^{c_i}$ という形のものを求めてください。
"""

# TODO: move and split this module?

import abc
import fractions
import re
from logging import getLogger
from typing import *

import ply.lex as lex
import ply.yacc as yacc

from onlinejudge_template.types import *

logger = getLogger(__name__)


class ExprParserError(AnalyzerError):
    pass


class _Expr(abc.ABC):
    pass


class _Variable(_Expr):
    """_Variable represents a symbol whose value is not fixed.
    """
    def __init__(self, name: str, *args: _Expr):
        self.name = name
        self.args = args

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.name == other.name and self.args == other.args


class _Function(_Expr):
    """_Function represents an n-ary symbol (n >= 1) whose value is fixed.
    """

    ADD = '__add__'
    SUB = '__sub__'
    MUL = '__mul__'
    DIV = '__div__'
    NEG = '__neg__'

    def __init__(self, value: str, *args: _Expr):
        self.value = value
        self.args = args

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value and self.args == other.args


class _Constant(_Expr):
    """_Constant represents a 0-ary symbol whose value is fixed.
    """
    def __init__(self, value: int):
        self.value = value

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.value == other.value


_tokens = (
    'IDENT',
    'NUMBER',
    'UNDERSCORE',
    'LBRACE',
    'RBRACE',
    'COMMA',
    'LPAREN',
    'RPAREN',
    'ADD',
    'SUB',
    'MUL',
    'DIV',
)


def _build_lexer() -> lex.Lexer:
    tokens = _tokens

    t_ignore = ' '

    def t_error(t: lex.LexToken) -> None:
        raise ExprParserError("lexer: unexpected character: '{}' at line {} column {}".format(t.value[0], t.lineno, t.lexpos))

    t_IDENT = r'[A-Za-z]+'
    t_NUMBER = r'[0-9]+'

    t_UNDERSCORE = r'_'
    t_LBRACE = r'{'
    t_RBRACE = r'}'
    t_COMMA = r','

    t_LPAREN = r'\('
    t_RPAREN = r'\)'

    t_ADD = r'\+'
    t_SUB = r'-'
    t_MUL = r'\*'
    t_DIV = r'/'

    return lex.lex()


def _build_parser(*, input: str) -> yacc.LRParser:
    tokens = _tokens

    def find_column(lexpos: int) -> int:
        line_start = input.rfind('\n', 0, lexpos) + 1
        return lexpos - line_start + 1

    def loc(p: yacc.YaccProduction) -> Dict[str, int]:
        return {
            'line': p.lineno(1),
            'column': find_column(p.lexpos(1)),
        }

    def p_expr(p: yacc.YaccProduction) -> None:
        """expr : expr ADD term
                | expr SUB term
                | term"""
        if len(p) == 4:
            op = {'+': _Function.ADD, '-': _Function.SUB}[p[2]]
            p[0] = _Function(op, p[1], p[3])
        elif len(p) == 2:
            p[0] = p[1]

    def p_exprs(p: yacc.YaccProduction) -> None:
        """exprs : expr COMMA exprs
                 | expr"""
        if len(p) == 4:
            p[0] = (p[1], *p[3])
        elif len(p) == 2:
            p[0] = (p[1], )

    def p_term(p: yacc.YaccProduction) -> None:
        """term : term MUL factor
                | term DIV factor
                | SUB term
                | factor"""
        if len(p) == 4:
            op = {'*': _Function.MUL, '/': _Function.DIV}[p[2]]
            p[0] = _Function(op, p[1], p[3])
        elif len(p) == 3:
            p[0] = _Function(_Function.NEG, p[2])
        elif len(p) == 2:
            p[0] = p[1]

    def p_factor(p: yacc.YaccProduction) -> None:
        """factor : number variable
                  | number
                  | variable
                  | LPAREN expr RPAREN
                  | number LPAREN expr RPAREN"""
        if len(p) == 3:
            p[0] = _Function(_Function.MUL, p[1], p[2])
        elif len(p) == 2:
            p[0] = p[1]
        elif len(p) == 4:
            p[0] = p[2]
        elif len(p) == 5:
            p[0] = _Function(_Function.MUL, p[1], p[3])

    def p_number(p: yacc.YaccProduction) -> None:
        """number : NUMBER"""
        p[0] = _Constant(int(p[1]))

    def p_variable(p: yacc.YaccProduction) -> None:
        """variable : IDENT UNDERSCORE IDENT
                    | IDENT UNDERSCORE number
                    | IDENT UNDERSCORE LBRACE exprs RBRACE
                    | IDENT"""
        if len(p) == 4 and isinstance(p[3], str):
            p[0] = _Variable(p[1], _Variable(p[3]))
        elif len(p) == 4 and isinstance(p[3], _Expr):
            p[0] = _Variable(p[1], p[3])
        elif len(p) == 6:
            p[0] = _Variable(p[1], *p[4])
        elif len(p) == 2:
            p[0] = _Variable(p[1])

    def p_error(t: Optional[lex.LexToken]) -> None:
        if t is None:
            raise ExprParserError("parser: something wrong")
        else:
            raise ExprParserError("parser: unexpected token: {} \"{}\" at line {} column {}".format(t.type, t.value, t.lineno, find_column(t.lexpos)))

    return yacc.yacc(debug=False, write_tables=False)


def _parse(s: str) -> _Expr:
    """
    :raises ExprParserError:
    """

    try:
        lexer = _build_lexer()
        lexer.input(s)
        parser = _build_parser(input=s)
        return parser.parse(lexer=lexer)
    except ExprParserError as e:
        logger.debug('failed to parse {}: {}'.format(repr(s), e))
        raise


def _format(e: _Expr) -> str:
    def with_paren(s: str, *, cur_prec: int, prev_prec: int, paren: str) -> str:
        if cur_prec >= prev_prec:
            return s
        if paren == '()':
            return '(' + s + ')'
        elif paren == '{}':
            return '{' + s + '}'
        else:
            assert False

    def go(e: _Expr, *, prec: int, paren: str = '()') -> str:
        if isinstance(e, _Variable):
            if len(e.args) == 0:
                return e.name
            elif len(e.args) == 1:
                return e.name + '_' + go(e.args[0], prec=2, paren='{}')
            else:
                return e.name + '_{' + ', '.join(map(lambda arg: go(arg, prec=0), e.args)) + '}'
        elif isinstance(e, _Function):
            if e.value == _Function.ADD and len(e.args) == 2:
                return with_paren(go(e.args[0], prec=1) + ' + ' + go(e.args[1], prec=1), cur_prec=1, prev_prec=prec, paren=paren)
            elif e.value == _Function.SUB and len(e.args) == 2:
                return with_paren(go(e.args[0], prec=1) + ' - ' + go(e.args[1], prec=1), cur_prec=1, prev_prec=prec, paren=paren)
            elif e.value == _Function.MUL and len(e.args) == 2:
                return with_paren(go(e.args[0], prec=2) + ' * ' + go(e.args[1], prec=2), cur_prec=2, prev_prec=prec, paren=paren)
            elif e.value == _Function.DIV and len(e.args) == 2:
                return with_paren(go(e.args[0], prec=2) + ' / ' + go(e.args[1], prec=2), cur_prec=2, prev_prec=prec, paren=paren)
            elif e.value == _Function.NEG and len(e.args) == 1:
                return with_paren('- ' + go(e.args[0], prec=2), cur_prec=2, prev_prec=prec, paren=paren)
            else:
                assert False
        elif isinstance(e, _Constant):
            return str(e.value)
        else:
            assert False

    return go(e, prec=0)


def _get_subscripted_value(value: Union[int, List[int], List[List[int]], List[List[List[int]]]], args: List[int], *, name_for_error_message: str) -> int:
    """
    :raises ExprParserError:
    """

    result: Any = value
    for depth, index in enumerate(args):
        if not isinstance(result, list):
            raise ExprParserError('{} is expected to have type int^{} -> int, but actually has type int^{} -> {}'.format(name_for_error_message, len(args), depth + 1, type(result).__name__))
        result = result[index]
    if not isinstance(result, int):
        raise ExprParserError('{} is expected to have type int^{} -> int, but actually has type int^{} -> {}'.format(name_for_error_message, len(args), len(args), type(result).__name__))
    return result


def evaluate(s: Expr, *, env: Mapping[VarName, Union[int, List[int], List[List[int]], List[List[List[int]]]]] = {}) -> Optional[int]:
    """evaluate converts the given expr to an integer.
    """
    def go(e: _Expr) -> fractions.Fraction:
        if isinstance(e, _Variable):
            if e.name not in env:
                raise ExprParserError('{} is not defined'.format(e.name))
            args: List[fractions.Fraction] = list(map(go, e.args))
            indices: List[int] = []
            for arg in args:
                if arg.denominator != 1:
                    raise ExprParserError('indices must be an integer, not fraction: {}[{}]'.format(e.name, ', '.join(map(str, args))))
                indices.append(arg.numerator)
            return fractions.Fraction(_get_subscripted_value(env[VarName(e.name)], indices, name_for_error_message=e.name))
        elif isinstance(e, _Function):
            args = list(map(go, e.args))
            if e.value == _Function.ADD and len(e.args) == 2:
                return args[0] + args[1]
            elif e.value == _Function.SUB and len(e.args) == 2:
                return args[0] - args[1]
            elif e.value == _Function.MUL and len(e.args) == 2:
                return args[0] * args[1]
            elif e.value == _Function.DIV and len(e.args) == 2:
                return args[0] / args[1]
            elif e.value == _Function.NEG and len(e.args) == 1:
                return -args[0]
            else:
                assert False
        elif isinstance(e, _Constant):
            return fractions.Fraction(e.value)
        else:
            assert False

    try:
        expr = _parse(s)
    except ExprParserError as e:
        logger.debug('failed to parse {}: {}'.format(repr(s), e))
        return None
    try:
        evaluated = go(expr)
    except ExprParserError as e:
        logger.debug('failed to evaluate {} in {}: {}'.format(repr(s), env, e))
        return None
    if evaluated.denominator != 1:
        logger.debug('failed to evaluate {} in {}: {} is not an integer'.format(repr(s), env, evaluated))
        return None
    return evaluated.numerator


def _convert_to_dnf(e: _Expr) -> List[Tuple[List[_Expr], List[_Expr]]]:
    """_convert_to_dnf converts exprs to a format like disjunction normal form (DNF).

    This also simplifies the subscripted exprs.
    """

    # TODO: Rename variables. We can see $a_i + 2 a_{i + 1} + 3 a_{i + 2}$ as $x + 2 y + 3 z$ or just $v_0 + 2 v_1 + 3 v_2$. Replacing the variables with their indices will make the implementation simpler.
    if isinstance(e, _Variable):
        args = list(map(_simplify_expr, e.args))
        return [([_Variable(e.name, *args)], [])]
    elif isinstance(e, _Function):
        if e.value == _Function.ADD and len(e.args) == 2:
            lhs = _convert_to_dnf(e.args[0])
            rhs = _convert_to_dnf(e.args[1])
            return lhs + rhs
        elif e.value == _Function.SUB and len(e.args) == 2:
            lhs = _convert_to_dnf(e.args[0])
            rhs = _convert_to_dnf(e.args[1])
            return lhs + [([_Constant(-1), *num], den) for num, den in rhs]
        elif e.value == _Function.MUL and len(e.args) == 2:
            lhs = _convert_to_dnf(e.args[0])
            rhs = _convert_to_dnf(e.args[1])
            return sum([[(num1 + num2, den1 + den2) for num2, den2 in rhs] for num1, den1 in lhs], [])
        elif e.value == _Function.DIV and len(e.args) == 2:
            lhs = _convert_to_dnf(e.args[0])
            rhs = _convert_to_dnf(e.args[1])
            return sum([[(num1 + den2, den1 + num2) for num2, den2 in rhs] for num1, den1 in lhs], [])
        elif e.value == _Function.NEG and len(e.args) == 1:
            rhs = _convert_to_dnf(e.args[0])
            return [([_Constant(-1), *num], den) for num, den in rhs]
        else:
            assert False
    elif isinstance(e, _Constant):
        return [([e], [])]
    else:
        assert False


def _simplify_dnf(dnf: List[Tuple[List[_Expr], List[_Expr]]]) -> Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], fractions.Fraction]:
    """
    :raises ExprParserError:
    """

    freq: Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], fractions.Fraction] = {}

    for old_num, old_den in dnf:
        # collect constants
        coeff = fractions.Fraction(1)
        num = []
        den = []
        for e in old_num:
            if isinstance(e, _Variable):
                num.append(_format(e))
            elif isinstance(e, _Constant):
                coeff *= e.value
            else:
                assert False
        for e in old_den:
            if isinstance(e, _Variable):
                str_e = _format(e)
                if str_e in num:
                    num.remove(str_e)
                else:
                    den.append(str_e)
            elif isinstance(e, _Constant):
                if e.value == 0:
                    raise ExprParserError('division by zero')
                coeff /= e.value
            else:
                assert False

        # count up
        str_num = tuple(sorted(num))
        str_den = tuple(sorted(den))
        if (str_num, str_den) not in freq:
            freq[(str_num, str_den)] = fractions.Fraction(0)
        freq[(str_num, str_den)] += coeff

    return freq


def _convert_from_dnf(freq: Dict[Tuple[Tuple[str, ...], Tuple[str, ...]], fractions.Fraction]) -> _Expr:
    """
    :raises ExprParserError:
    """

    exprs: List[str] = []
    factors = sorted(freq.items())
    if factors and not factors[0][0][0] and not factors[0][0][1]:
        # move the constant factor to the back
        factors = factors[1:] + factors[:1]
    for (num, den), coeff in factors:
        if coeff == 0:
            continue
        if coeff.denominator != 1:
            raise ExprParserError('coefficient is not an integer: {} \\prod {} / \\prod {}'.format(coeff, num, den))

        neg = False
        if coeff < 0:
            neg = True
            coeff = -coeff

        # construct a string for a factor
        s = ''
        if coeff == 1:
            pass
        else:
            s += str(coeff.numerator)
        if s and num:
            s += ' * '
        s += ' * '.join(['(' + e + ')' for e in num])
        if not s:
            s += '1'
        if den:
            s += ' / '
        s += ' / '.join(['(' + e + ')' for e in den])
        if neg:
            s = '- ' + s
        if exprs and not s.startswith('-'):
            s = '+ ' + s
        exprs.append(s)
    s = ' '.join(exprs)
    if not s:
        s += '0'
    return _parse(s)


def _simplify_expr(e: _Expr) -> _Expr:
    """
    :raises ExprParserError:
    """

    return _convert_from_dnf(_simplify_dnf(_convert_to_dnf(e)))


def simplify(s: Expr) -> Expr:
    """simplify converts the given expr to a simple expr.
    """

    try:
        expr = _parse(s)
    except ExprParserError as e:
        logger.debug('failed to parse %s: %s', repr(s), e)
        return s
    try:
        simplified = _simplify_expr(expr)
    except ExprParserError as e:
        logger.debug('failed to simplify %s: %s', repr(s), e)
        return s
    return Expr(_format(simplified))


def format_subscripted_variable(*, name: str, indices: List[str]) -> str:
    """format_subscripted_variable constructs a single expr from a variable name and indices

    :raises ExprParserError: if not a variable
    """

    expr = _parse(name)
    if not isinstance(expr, _Variable) or expr.args:
        raise ExprParserError('not a variable name: {}'.format(name))
    return _format(_Variable(expr.name, *map(_parse, indices)))


def parse_subscripted_variable(s: str) -> Tuple[str, List[str]]:
    """parse_subscripted_variable is an inverse of format_subscripted_variable.

    :raises ExprParserError: if not a variable
    """

    expr = _parse(s)
    if not isinstance(expr, _Variable):
        raise ExprParserError('not a subscripted variable: {}'.format(s))
    return expr.name, list(map(_format, expr.args))


def rename_variables_in_expr(expr: Expr, *, replace: Dict[VarName, VarName]) -> Expr:
    """
    :raises ExprParserError:
    """

    pattern = r'[A-Za-z]+|[^A-Za-z]+'
    s = []
    for c in re.findall(pattern, str(expr)):
        if c.isalpha() and VarName(c) in replace:
            s.append(str(replace[VarName(c)]))
        else:
            s.append(c)
    return Expr(_format(_parse(''.join(s))))
