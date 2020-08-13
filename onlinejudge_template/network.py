"""
the module to access networks

この module はネットワークアクセスを行い、問題の HTML やサンプルケースを取得します。
"""

from logging import getLogger
from typing import *

import requests

import onlinejudge
import onlinejudge.utils
from onlinejudge_template.types import *

logger = getLogger(__name__)


def download_html(url: str, *, session: Optional[requests.Session] = None) -> bytes:
    session = session or onlinejudge.utils.get_default_session()
    resp = session.get(url)
    logger.debug('HTTP response: %s', resp)
    resp.raise_for_status()
    return resp.content


def download_sample_cases(url: str, *, session: Optional[requests.Session] = None) -> Optional[List[SampleCase]]:
    session = session or onlinejudge.utils.get_default_session()
    try:
        problem = onlinejudge.dispatch.problem_from_url(url)
        assert problem is not None
        sample_cases = problem.download_sample_cases(session=session)
        return [SampleCase(input=case.input_data, output=case.output_data) for case in sample_cases]
    except Exception as e:
        logger.error('downloading sample cases failed: %s', e)
        return None
