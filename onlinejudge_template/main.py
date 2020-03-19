import argparse
import sys
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import onlinejudge_template.analyzer.combined
import onlinejudge_template.generator

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

    url = args.url
    html = onlinejudge_template.analyzer.combined.download_html(args.url)

    # analyze
    resources = onlinejudge_template.analyzer.combined.prepare_from_html(html, url=url)
    analyzed = onlinejudge_template.analyzer.combined.run(resources)

    # generate
    code = onlinejudge_template.generator.run(analyzed, template_file=args.template)
    sys.stdout.buffer.write(code)


if __name__ == '__main__':
    main()
