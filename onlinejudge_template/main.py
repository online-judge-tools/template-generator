import argparse
from logging import DEBUG, INFO, basicConfig, getLogger

import onlinejudge_template.analyzer

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

    onlinejudge_template.analyzer.run(args.url, template=args.template)


if __name__ == '__main__':
    main()
