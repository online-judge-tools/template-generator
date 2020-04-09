import argparse
import sys
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import onlinejudge_template.analyzer.combined
import onlinejudge_template.generator
import onlinejudge_template.network

import onlinejudge.utils

logger = getLogger(__name__)


def main(args: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-t', '--template', default='main.cpp')
    parser.add_argument('-v', '--verbose', action='store_true')
    parser.add_argument('-c', '--cookie', default=onlinejudge.utils.default_cookie_path)
    parsed = parser.parse_args(args=args)

    if parsed.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)

    # download
    url = parsed.url
    with onlinejudge.utils.with_cookiejar(onlinejudge.utils.get_default_session(), path=parsed.cookie) as session:
        html = onlinejudge_template.network.download_html(url, session=session)
        sample_cases = onlinejudge_template.network.download_sample_cases(url, session=session)

    # analyze
    resources = onlinejudge_template.analyzer.combined.prepare_from_html(html, url=url, sample_cases=sample_cases)
    analyzed = onlinejudge_template.analyzer.combined.run(resources)

    # generate
    code = onlinejudge_template.generator.run(analyzed, template_file=parsed.template)
    sys.stdout.buffer.write(code)


if __name__ == '__main__':
    main()
