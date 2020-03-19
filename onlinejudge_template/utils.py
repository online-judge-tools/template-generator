import sympy
import sympy.parsing.sympy_parser as sympy_parser


def simplify(s: str) -> str:
    transformations = sympy_parser.standard_transformations + (sympy_parser.implicit_multiplication_application, )
    local_dict = {'N': sympy.Symbol('N')}
    expr = sympy_parser.parse_expr(s, local_dict=local_dict, transformations=transformations)
    return str(expr)
