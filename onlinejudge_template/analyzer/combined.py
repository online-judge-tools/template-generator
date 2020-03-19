from logging import getLogger
from typing import *

import onlinejudge_template.analyzer.constants
import onlinejudge_template.analyzer.html
import onlinejudge_template.analyzer.parser
import onlinejudge_template.analyzer.simple_patterns
import onlinejudge_template.analyzer.typing
import onlinejudge_template.analyzer.variables
from onlinejudge_template.types import *

logger = getLogger(__name__)


def prepare_from_html(html: bytes, *, url: str, sample_cases: Optional[List[SampleCase]] = None) -> AnalyzerResources:
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
        sample_cases=sample_cases,
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
    elif resources.sample_cases:
        input_samples = [case.input for case in resources.sample_cases]
        input_format = onlinejudge_template.analyzer.simple_patterns.guess_format_with_pattern_matching(instances=input_samples)

    output_format: Optional[FormatNode] = None
    if resources.output_format_string is not None:
        try:
            output_format = onlinejudge_template.analyzer.parser.run(resources.output_format_string)
        except AnalyzerError as e:
            logger.error('output analyzer failed: %s', e)
        except NotImplementedError as e:
            logger.error('output analyzer failed: %s', e)
    elif resources.sample_cases:
        output_samples = [case.output for case in resources.sample_cases]
        output_format = onlinejudge_template.analyzer.simple_patterns.guess_format_with_pattern_matching(instances=output_samples)

    input_variables: Optional[Dict[str, VarDecl]] = None
    if input_format is not None:
        try:
            input_variables = onlinejudge_template.analyzer.variables.list_declared_variables(input_format)
        except AnalyzerError as e:
            logger.error('input analyzer failed: %s', e)

    output_variables: Optional[Dict[str, VarDecl]] = None
    if output_format is not None:
        try:
            output_variables = onlinejudge_template.analyzer.variables.list_declared_variables(output_format)
        except AnalyzerError as e:
            logger.error('output analyzer failed: %s', e)

    if input_format is not None and input_variables is not None and resources.sample_cases:
        input_samples = [case.input for case in resources.sample_cases]
        try:
            input_types = onlinejudge_template.analyzer.typing.infer_types_from_instances(input_format, variables=input_variables, instances=input_samples)
            input_variables = onlinejudge_template.analyzer.typing.update_variables_with_types(variables=input_variables, types=input_types)
        except AnalyzerError as e:
            logger.error('input analyzer failed: %s', e)

    if output_format is not None and output_variables is not None and resources.sample_cases:
        output_samples = [case.output for case in resources.sample_cases]
        try:
            output_types = onlinejudge_template.analyzer.typing.infer_types_from_instances(output_format, variables=output_variables, instances=output_samples)
            output_variables = onlinejudge_template.analyzer.typing.update_variables_with_types(variables=output_variables, types=output_types)
        except AnalyzerError as e:
            logger.error('output analyzer failed: %s', e)

    constants: Dict[str, ConstantDecl] = {}
    if resources.html is not None or resources.sample_cases:
        constants.update(onlinejudge_template.analyzer.constants.list_constants(html=resources.html, sample_cases=resources.sample_cases))

    return AnalyzerResult(
        resources=resources,
        input_format=input_format,
        output_format=output_format,
        input_variables=input_variables,
        output_variables=output_variables,
        constants=constants,
    )
