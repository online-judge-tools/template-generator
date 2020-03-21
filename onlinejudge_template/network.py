"""
the module to access networks

この module はネットワークアクセスを行い、問題の HTML やサンプルケースを取得します。
"""

from logging import getLogger
from typing import *

import requests
from onlinejudge_template.types import *

import onlinejudge

logger = getLogger(__name__)


def download_html(url: str) -> bytes:
    resp = requests.get(url)
    logger.debug('HTTP response: %s', resp)
    resp.raise_for_status()
    return resp.content


def download_sample_cases(url: str) -> Optional[List[SampleCase]]:
    try:
        problem = onlinejudge.dispatch.problem_from_url(url)
        sample_cases = problem.download_sample_cases()
        return [SampleCase(input=case.input_data, output=case.output_data) for case in sample_cases]
    except Exception as e:
        logger.error('downloading sample cases failed: %s', e)
        return None
