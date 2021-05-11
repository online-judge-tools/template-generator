"""
the module to detect whether the style is multiple cases or not in Codeforces
"""

import re
import urllib.parse
from logging import getLogger
from typing import *

import bs4

from onlinejudge_template.types import *

logger = getLogger(__name__)


class CodeforcesParserError(AnalyzerError):
    pass


def is_codeforces_url(url: str) -> bool:
    result = urllib.parse.urlparse(url)
    return result.netloc == 'codeforces.com'


def has_multiple_testcases(html: bytes, *, url: str) -> bool:
    # parse HTML
    soup = bs4.BeautifulSoup(html, 'html.parser')
    input_specifications = soup.find_all('div', class_='input-specification')
    if len(input_specifications) != 1:
        logger.error("""<div class="input-specification"> is not found or not unique.""")
        return False
    input_specification = input_specifications[0]

    logger.debug('parse Input section')
    p = input_specification.find('p')
    if p is None:
        logger.error("""There are no <p> in the Input section.""")
        return False
    text = p.text

    # parse the first paragraph
    logger.debug('parse the first paragraph: %s', text)
    pattern = r"""[Tt]he +first +line.*integer.*\$t\$.*(number +of.*test|test +cases)|multiple +test +cases"""
    return bool(re.search(pattern, text))
