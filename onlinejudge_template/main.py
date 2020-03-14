import argparse
import sys
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import onlinejudge_template.analyzer
import onlinejudge_template.analyzer.html
import onlinejudge_template.generator
from onlinejudge_template.analyzer import FormatNode

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

    html = onlinejudge_template.analyzer.html.download_html(args.url)

    # analyze input
    input_node: Optional[FormatNode] = None
    try:
        input_format_string = onlinejudge_template.analyzer.html.parse_input_format_string(html, url=args.url)
        logger.debug('input format string: %s', repr(input_format_string))
        input_node = onlinejudge_template.analyzer.run(input_format_string)
    except onlinejudge_template.analyzer.TemplateGeneratorError as e:
        logger.error('input analyzer failed: %s', e)
    except NotImplementedError as e:
        logger.error('input analyzer failed: %s', e)

    # analyze output
    output_node: Optional[FormatNode] = None
    try:
        output_format_string = onlinejudge_template.analyzer.html.parse_output_format_string(html, url=args.url)
        logger.debug('output format string: %s', repr(output_format_string))
        output_node = onlinejudge_template.analyzer.run(output_format_string)
    except onlinejudge_template.analyzer.TemplateGeneratorError as e:
        logger.error('output analyzer failed: %s', e)
    except NotImplementedError as e:
        logger.error('output analyzer failed: %s', e)

    code = onlinejudge_template.generator.run(input_node, output_node, template_file=args.template)
    sys.stdout.buffer.write(code)


if __name__ == '__main__':
    main()
