"""
the module to find the input format string written with ``<pre>`` tags from HTML

この module は HTML を解析し ``<pre>`` タグに囲まれた入力フォーマット文字列を発見します。

たとえば `AtCoder Grand Contest 038: F - Two Permutations <https://atcoder.jp/contests/agc038/tasks/agc038_f>`_ の HTML は
::

    <h3>Input</h3><p>Input is given from Standard Input in the following format:</p>
    <pre><var>N</var>
    <var>P_0</var> <var>P_1</var> <var>\cdots</var> <var>P_{N-1}</var>
    <var>Q_0</var> <var>Q_1</var> <var>\cdots</var> <var>Q_{N-1}</var>
    </pre>

という部分文字列を含みますが、ここから次のような文字列を抜き出します。
::

    N
    P_0 P_1 \cdots P_{N-1}
    Q_0 Q_1 \cdots Q_{N-1}
"""

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
    """
    :param kind: ``"in"`` or ``"out"``

    .. todo::
       現状は ``<var>`` や ``</var>`` を消去しているが残す。構文解析時に利用できるため。
    """

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
