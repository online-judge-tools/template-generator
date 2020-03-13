import argparse
import sys
from logging import DEBUG, INFO, basicConfig, getLogger

import onlinejudge_template.analyzer
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

    soup = onlinejudge_template.analyzer.download_html(args.url)
    node = onlinejudge_template.analyzer.run(soup, url=args.url)
    code = onlinejudge_template.generator.run(node, template_file=args.template)
    sys.stdout.buffer.write(code)


if __name__ == '__main__':
    main()
