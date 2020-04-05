from typing import *

from onlinejudge_template.types import *


def get_analyzed(data: Dict['str', Any]) -> AnalyzerResult:
    return data['analyzed']


def get_indent(data: Dict['str', Any]) -> str:
    return data['config'].get('indent', ' ' * 4)
