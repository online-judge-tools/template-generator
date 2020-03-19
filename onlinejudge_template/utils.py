import re
from typing import *

import sympy
import sympy.parsing.sympy_parser as sympy_parser


def simplify(s: str, env: Set[str] = set()) -> str:
    transformations = sympy_parser.standard_transformations + (sympy_parser.implicit_multiplication_application, )
    local_dict = {name: sympy.Symbol(name) for name in (env | set(['N']))}
    expr = sympy_parser.parse_expr(s, local_dict=local_dict, transformations=transformations)
    return str(expr)


def evaluate(s: str, *, env: Dict[str, int]) -> Optional[int]:
    for name, value in env.items():
        s = re.sub(r'\b' + re.escape(name) + r'\b', str(value), s)
    try:
        return int(simplify(s))
    except ValueError:
        return None
