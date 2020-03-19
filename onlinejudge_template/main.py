import argparse
import sys
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import onlinejudge_template.analyzer.combined
import onlinejudge_template.generator
import onlinejudge_template.network

logger = getLogger(__name__)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-t', '--template', default='template.cpp')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)

    # download
    url = args.url
    html = onlinejudge_template.network.download_html(url)
    sample_cases = onlinejudge_template.network.download_sample_cases(url)

    # analyze
    resources = onlinejudge_template.analyzer.combined.prepare_from_html(html, url=url, sample_cases=sample_cases)
    analyzed = onlinejudge_template.analyzer.combined.run(resources)

    # generate
    code = onlinejudge_template.generator.run(analyzed, template_file=args.template)
    sys.stdout.buffer.write(code)


if __name__ == '__main__':
    main()
