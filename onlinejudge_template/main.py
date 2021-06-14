import argparse
import sys
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import colorlog

import onlinejudge.dispatch
import onlinejudge.utils
import onlinejudge_template.analyzer.combined as analyzer
import onlinejudge_template.generator._main as generator
import onlinejudge_template.network as network

logger = getLogger(__name__)


def main(args: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-t', '--template', default='main.cpp')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--cookie', default=onlinejudge.utils.default_cookie_path)
    parsed = parser.parse_args(args=args)

    # configure logging
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s%(levelname)s%(reset)s:%(name)s:%(message)s'))
    level = INFO
    if parsed.verbose:
        level = DEBUG
    basicConfig(level=level, handlers=[handler])

    exceptions: List[Exception] = []

    # download
    url = parsed.url
    problem = onlinejudge.dispatch.problem_from_url(url)
    if problem is not None:
        url = problem.get_url()  # normalize url
        url = url.replace('judge.yosupo.jp', 'old.yosupo.jp')  # TODO: support the new pages
    logger.debug('url: %s', url)
    try:
        with onlinejudge.utils.with_cookiejar(onlinejudge.utils.get_default_session(), path=parsed.cookie) as session:
            html = network.download_html(url, session=session)
            sample_cases = network.download_sample_cases(url, session=session)
    except Exception as e:
        exceptions.append(e)
        logger.error('failed to download sample cases')
        html = b''
        sample_cases = []
    logger.debug('sample cases: %s', sample_cases)

    # analyze
    resources = analyzer.prepare_from_html(html, url=url, sample_cases=sample_cases)
    logger.debug('analyzer resources: %s', resources._replace(html=b'...skipped...'))
    try:
        analyzed = analyzer.run(resources)
    except Exception as e:
        exceptions.append(e)
        logger.exception('failed to analyze the problem')
        analyzed = analyzer.get_empty_analyzer_result(resources)
    logger.debug('analyzed result: %s', analyzed._replace(resources=analyzed.resources._replace(html=b'...skipped...')))

    # generate
    try:
        code = generator.run(analyzed, template_file=parsed.template)
        sys.stdout.buffer.write(code)
    except Exception as e:
        exceptions.append(e)
        logger.exception('failed to generate code')

    if exceptions:
        raise exceptions[0]


if __name__ == '__main__':
    main()
