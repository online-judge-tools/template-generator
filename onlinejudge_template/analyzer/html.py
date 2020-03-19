from logging import getLogger
from typing import *

import bs4
from onlinejudge_template.types import AnalyzerError

logger = getLogger(__name__)


class HTMLParserError(AnalyzerError):
    pass


table = {
    'in': ('Input', 'Input / 入力', '入力'),
    'out': ('Output', 'Output / 出力', '出力'),
}


def parse_generic_format_string(html: bytes, *, kind: str, url: str) -> str:
    soup = bs4.BeautifulSoup(html, 'html.parser')
    logger.debug('parsed HTML: %s...', repr(str(soup))[:200])

    if 'atcoder.jp' in url:
        for h3 in soup.find_all('h3'):
            if h3.string in table[kind]:
                pre = h3.parent.find('pre')
                if pre:
                    s = ''
                    for it in pre:
                        s += it.string or it
                    return s.strip() + '\r\n'
        raise HTMLParserError

    elif 'yukicoder.me' in url:
        for h4 in soup.find_all('h4'):
            if h4.string in table[kind]:
                pre = h4.parent.find('pre')
                if pre:
                    return pre.string.strip() + '\n'
        raise HTMLParserError

    elif 'judge.yosupo.jp' in url:
        for h2 in soup.find_all('h2'):
            if h2.string in table[kind]:
                pre = h2.find_next_sibling('pre')
                if pre:
                    return pre.string.strip() + '\n'
        raise HTMLParserError

    else:
        raise NotImplementedError


def parse_input_format_string(html: bytes, *, url: str) -> str:
    return parse_generic_format_string(html, kind='in', url=url)


def parse_output_format_string(html: bytes, *, url: str) -> str:
    return parse_generic_format_string(html, kind='out', url=url)
