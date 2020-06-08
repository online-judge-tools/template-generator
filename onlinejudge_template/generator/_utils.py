from typing import *

from onlinejudge_template.types import *


def get_analyzed(data: Dict['str', Any]) -> AnalyzerResult:
    return data['analyzed']


def get_indent(data: Dict['str', Any]) -> str:
    return data['config'].get('indent', ' ' * 4)


# TODO: refactoring
def _filter_ignored_variables(decls: Dict[str, VarDecl], *, data: Dict[str, Any]) -> Dict[str, VarDecl]:
    if get_analyzed(data).topcoder_class_definition is None:
        return decls
    return {name: decl for name, decl in decls.items() if not name.endswith('_length')}
