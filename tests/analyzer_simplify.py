import unittest

import onlinejudge_template.analyzer.simplify as simplify
from onlinejudge_template.analyzer.simplify import _Constant, _Function, _Variable
from onlinejudge_template.types import *

var = _Variable
con = _Constant
add = lambda e1, e2: _Function(_Function.ADD, e1, e2)
sub = lambda e1, e2: _Function(_Function.SUB, e1, e2)
mul = lambda e1, e2: _Function(_Function.MUL, e1, e2)
div = lambda e1, e2: _Function(_Function.DIV, e1, e2)
neg = lambda e: _Function(_Function.NEG, e)


class TestExprParser(unittest.TestCase):
    """TestExprParser is a class for unit tests for the parser of expressions.
    """
    def test_simple(self) -> None:
        expr = 'a + 3'
        expected = add(var('a'), con(3))

        actual = simplify._parse(expr)
        self.assertEqual(actual, expected)

    def test_complicated(self) -> None:
        expr = '(- a_{i,2j} + 3 b_j) * ccc'
        a = neg(var('a', var('i'), mul(con(2), var('j'))))
        b = mul(con(3), var('b', var('j')))
        c = var('ccc')
        expected = mul(add(a, b), c)

        actual = simplify._parse(expr)
        self.assertEqual(actual, expected)

    def test_parens(self) -> None:
        expr = '(x + 1) * (y + 1) - (2 (x * y) + 1)'
        x = add(var('x'), con(1))
        y = add(var('y'), con(1))
        z = add(mul(con(2), mul(var('x'), var('y'))), con(1))
        expected = sub(mul(x, y), z)

        actual = simplify._parse(expr)
        self.assertEqual(actual, expected)


class TestExprFormatter(unittest.TestCase):
    """TestExprFormatter is a class for unit tests for the formatter of expressions.
    """
    def test_simple(self) -> None:
        expr = add(var('a'), con(3))
        expected = 'a + 3'

        actual = simplify._format(expr)
        self.assertEqual(actual, expected)

    def test_complicated(self) -> None:
        a = neg(var('a', var('i'), mul(con(2), var('j'))))
        b = mul(con(3), var('b', var('j')))
        c = var('ccc')
        expr = mul(add(a, b), c)
        expected = '(- a_{i, 2 * j} + 3 * b_j) * ccc'

        actual = simplify._format(expr)
        self.assertEqual(actual, expected)


class TestExprEvaluation(unittest.TestCase):
    """TestExprEvaluation is a class for unit tests for the evaluation of expressions.
    """
    def test_simple(self) -> None:
        expr = 'a + 3'
        env = {
            'a': 4,
        }
        expected = 7

        actual = simplify.evaluate(expr, env=env)
        self.assertEqual(actual, expected)

    def test_complicated(self) -> None:
        expr = '- a_{i, 2 j} + 3 b_j + ccc'
        env = {
            'a': [[0, 1, 4], [0, 2, 8]],
            'b': [2, 3, 4],
            'ccc': 100,
            'i': 1,
            'j': 1,
        }
        expected = 101

        actual = simplify.evaluate(expr, env=env)
        self.assertEqual(actual, expected)

    def test_undefined_symbol(self) -> None:
        expr = 'a + 3'
        env = {
            'b': 3,
        }

        actual = simplify.evaluate(expr, env=env)
        self.assertIsNone(actual)


class TestExprSimplification(unittest.TestCase):
    """TestExprSimplification is a class for unit tests for the simplification of expressions.
    """
    def test_simple(self) -> None:
        expr = '(n + 1) + (n - 1)'
        expected = '2 * n'

        actual = simplify.simplify(expr)
        self.assertEqual(actual, expected)

    def test_const(self) -> None:
        expr = '2 * 3 * x - 5 * x'
        expected = 'x'

        actual = simplify.simplify(expr)
        self.assertEqual(actual, expected)

    def test_parens(self) -> None:
        expr = '(x + 1) * (y + 1) - (2 (x * y) + 1)'
        expected = 'x - x * y + y'

        actual = simplify.simplify(expr)
        self.assertEqual(actual, expected)

    def test_div(self) -> None:
        expr = 'n / 2 + n / 2'
        expected = 'n'

        actual = simplify.simplify(expr)
        self.assertEqual(actual, expected)

    def test_subscripted(self) -> None:
        expr = 'a _ {n + 1 - n} + a _ {n + 1 - (n - 1)} + a _ {n + 1 - (n - 2)} + dots + a _ {n + 1 - 2} + a _ {n + 1 - 1}'
        expected = 'a_1 + a_2 + a_3 + a_n + a_{n - 1} + dots'

        actual = simplify.simplify(expr)
        self.assertEqual(actual, expected)
