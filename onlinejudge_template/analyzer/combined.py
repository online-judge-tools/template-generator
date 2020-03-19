from logging import getLogger
from typing import *

import onlinejudge_template.analyzer.html
import onlinejudge_template.analyzer.parser
import requests
from onlinejudge_template.types import *

logger = getLogger(__name__)


def download_html(url: str) -> bytes:
    resp = requests.get(url)
    logger.debug('HTTP response: %s', resp)
    resp.raise_for_status()
    return resp.content


def prepare_from_html(html: bytes, *, url: str) -> AnalyzerResources:
    input_format_string: Optional[str] = None
    try:
        input_format_string = onlinejudge_template.analyzer.html.parse_input_format_string(html, url=url)
        logger.debug('input format string: %s', repr(input_format_string))
    except AnalyzerError as e:
        logger.error('input analyzer failed: %s', e)
    except NotImplementedError as e:
        logger.error('input analyzer failed: %s', e)

    output_format_string: Optional[str] = None
    try:
        output_format_string = onlinejudge_template.analyzer.html.parse_output_format_string(html, url=url)
        logger.debug('output format string: %s', repr(output_format_string))
    except AnalyzerError as e:
        logger.error('output analyzer failed: %s', e)
    except NotImplementedError as e:
        logger.error('output analyzer failed: %s', e)

    return AnalyzerResources(
        url=url,
        html=html,
        input_format_string=input_format_string,
        output_format_string=output_format_string,
        sample_cases=None,
    )


def run(resources: AnalyzerResources) -> AnalyzerResult:
    input_format: Optional[FormatNode] = None
    if resources.input_format_string is not None:
        try:
            input_format = onlinejudge_template.analyzer.parser.run(resources.input_format_string)
        except AnalyzerError as e:
            logger.error('input analyzer failed: %s', e)
        except NotImplementedError as e:
            logger.error('input analyzer failed: %s', e)

    ouput_format: Optional[FormatNode] = None
    if resources.output_format_string is not None:
        try:
            ouput_format = onlinejudge_template.analyzer.parser.run(resources.output_format_string)
        except AnalyzerError as e:
            logger.error('output analyzer failed: %s', e)
        except NotImplementedError as e:
            logger.error('output analyzer failed: %s', e)

    return AnalyzerResult(resources=resources, input_format=input_format, output_format=ouput_format)
