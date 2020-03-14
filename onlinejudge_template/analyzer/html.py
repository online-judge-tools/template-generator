from logging import getLogger
from typing import *

import bs4
import requests
from onlinejudge_template.analyzer import TemplateGeneratorError

logger = getLogger(__name__)


class HTMLParserError(TemplateGeneratorError):
    pass


def download_html(url: str) -> str:
    resp = requests.get(url)
    logger.debug('HTTP response: %s', resp)
    resp.raise_for_status()
    return resp.content.decode(resp.encoding)


table = {
    'in': ('Input', 'Input / 入力', '入力'),
    'out': ('Output', 'Output / 出力', '出力'),
}


def parse_generic_format_string(html: str, *, kind: str, url: str) -> str:
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


def parse_input_format_string(html: str, *, url: str) -> str:
    return parse_generic_format_string(html, kind='in', url=url)


def parse_output_format_string(html: str, *, url: str) -> str:
    return parse_generic_format_string(html, kind='out', url=url)
