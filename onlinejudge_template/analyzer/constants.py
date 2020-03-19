import re
from logging import getLogger
from typing import *

from onlinejudge_template.types import *

logger = getLogger(__name__)


def list_constants_from_html(html: bytes) -> Dict[str, ConstantDecl]:
    replace = [
        ("\\", ""),
        ("{", ""),
        ("}", ""),
        (",", ""),
        ("'", ""),
        (" ", ""),
        ("10^9+7", "1000000007"),
        ("10^9+9", "1000000009"),
    ]
    normalized = html.decode()
    for a, b in replace:
        normalized = normalized.replace(a, b)

    mod: Set[int] = set()
    for value in (10**9 + 7, 10**9 + 9, 998244353):
        if re.search(r'\b' + re.escape(str(value)) + r'\b', normalized):
            mod.add(value)
    logger.debug('MOD-like integers: %s', mod)

    constants: Dict[str, ConstantDecl] = {}
    if len(mod) == 1:
        constants['MOD'] = ConstantDecl(name='MOD', type=VarType.ValueInt, value=str(mod.pop()))
    return constants


def list_constants_from_sample_cases(sample_cases: List[SampleCase]) -> Dict[str, ConstantDecl]:
    yes: Set[str] = set()
    no: Set[str] = set()
    first: Set[str] = set()
    second: Set[str] = set()
    for case in sample_cases:
        for token in case.output.decode().split():
            if token.lower() in ("yes", "possible"):
                yes.add(token)
            if token.lower() in ("no", "impossible"):
                no.add(token)
            if token.lower() in ("first", "alice"):
                first.add(token)
            if token.lower() in ("second", "bob"):
                second.add(token)
    logger.debug('YES-like strings: %s', yes)
    logger.debug('NO-like strings: %s', no)
    logger.debug('Alice-like strings: %s', first)
    logger.debug('Bob-like strings: %s', second)

    constants: Dict[str, ConstantDecl] = {}
    if len(yes) == 1:
        constants['YES'] = ConstantDecl(name='YES', type=VarType.String, value=yes.pop())
    if len(no) == 1:
        constants['NO'] = ConstantDecl(name='NO', type=VarType.String, value=no.pop())
    if len(first) == 1:
        constants['FIRST'] = ConstantDecl(name='FIRST', type=VarType.String, value=first.pop())
    if len(second) == 1:
        constants['SECOND'] = ConstantDecl(name='SECOND', type=VarType.String, value=second.pop())
    return constants


def list_constants(*, html: Optional[bytes], sample_cases: Optional[List[SampleCase]]) -> Dict[str, ConstantDecl]:
    constants = {}
    if html is not None:
        constants.update(list_constants_from_html(html))
    if sample_cases is not None:
        constants.update(list_constants_from_sample_cases(sample_cases))
    return constants
