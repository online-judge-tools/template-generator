"""
the module to parse the class definition of problems of Topcoder from thier HTML
"""

import re
import urllib.parse
from logging import getLogger
from typing import *

import bs4

from onlinejudge_template.types import *

logger = getLogger(__name__)


class TopcoderParserError(AnalyzerError):
    pass


def is_topcoder_url(url: str) -> bool:
    result = urllib.parse.urlparse(url)
    return result.netloc == 'community.topcoder.com'


def _parse_topcoder_html(soup: bs4.BeautifulSoup) -> Dict[str, str]:
    problem_texts = soup.find_all('td', class_='problemText')
    if len(problem_texts) != 1:
        raise TopcoderParserError("""<td class="problemText"> is not found or not unique""")
    problem_text = problem_texts[0]

    # parse Definition section
    # format:
    #     <tr>...<h3>Definition</h3>...<tr>
    #     <tr><td>...</td>
    #         <td><table>
    #             ...
    #             <tr><td>Class:</td><td>...</td></tr>
    #             <tr><td>Method:</td><td>...</td></tr>
    #             ...
    #         </table></td></tr>
    logger.debug('parse Definition section')
    h3 = problem_text.find('h3', text='Definition')
    if h3 is None:
        raise TopcoderParserError("""<h3>Definition</h3> is not found""")
    definition = {}
    for key in ('Class', 'Method', 'Parameters', 'Returns', 'Method signature'):
        td = h3.parent.parent.next_sibling.find('td', class_='statText', text=key + ':')
        logger.debug('%s', td.parent)
        definition[key] = td.next_sibling.string
    return definition


def _parse_topcoder_method_signature(signature: str) -> Tuple[TopcoderType, List[Tuple[TopcoderType, str]]]:
    """
    .. code-block::

        signature ::= type ident '(' var-decls ')'
        type ::= atomic-type | atomic-type "[]"
        atomic-type ::= "int" | "double" | "String"
        ident ::= ...
        var-decls ::= var-decl | var-decls ',' var-decl
        var-decl ::= type ident
    """

    type_table = {
        'int': TopcoderType.Int,
        'long': TopcoderType.Long,
        'double': TopcoderType.Double,
        'String': TopcoderType.String,
        'int[]': TopcoderType.IntList,
        'long[]': TopcoderType.LongList,
        'double[]': TopcoderType.DoubleList,
        'String[]': TopcoderType.StringList,
    }

    m = re.match(r'^(\w+(?:\[\])?) \w+\((.*)\)$', signature)
    if not m:
        raise TopcoderParserError('failed to parse the "Method signature:"')
    return_type = type_table[m.group(1)]
    formal_arguments = []
    for decl in m.group(2).split(', '):
        type_, name = decl.split()
        formal_arguments.append((type_table[type_], name))
    return (return_type, formal_arguments)


def parse_topcoder_class_definition(html: bytes, *, url: str) -> TopcoderClassDefinition:
    """parse_topcoder_class_definition parses the Definition section of the problem from HTML.

    :raises TopcoderParserError:

    .. note::
        example: https://community.topcoder.com/stat?c=problem_statement&pm=11213
    """

    soup = bs4.BeautifulSoup(html, 'html.parser')
    definition = _parse_topcoder_html(soup)
    return_type, formal_arguments = _parse_topcoder_method_signature(definition['Method signature'])
    class_definition = TopcoderClassDefinition(
        class_name=definition['Class'],
        method_name=definition['Method'],
        formal_arguments=formal_arguments,
        return_type=return_type,
    )
    logger.debug('Topcoder Class Definition: %s', class_definition)
    return class_definition


def _convert_topcoder_node(type_: TopcoderType, name: str) -> FormatNode:
    if type_ in (TopcoderType.Int, TopcoderType.Long, TopcoderType.Double, TopcoderType.String):
        return SequenceNode(items=[
            ItemNode(name=name),
            NewlineNode(),
        ])
    elif type_ in (TopcoderType.IntList, TopcoderType.LongList, TopcoderType.DoubleList, TopcoderType.StringList):
        length_name = name + '_length'
        index_name = 'i'
        return SequenceNode(items=[
            ItemNode(name=length_name),
            LoopNode(name=index_name, size=length_name, body=ItemNode(name=name, indices=[index_name])),
            NewlineNode(),
        ])
    else:
        assert False


def convert_topcoder_class_definition_to_input_format(definition: TopcoderClassDefinition) -> FormatNode:
    items = []
    for type_, name in definition.formal_arguments:
        items.append(_convert_topcoder_node(type_, name))
    return SequenceNode(items=items)


def convert_topcoder_class_definition_to_output_format(definition: TopcoderClassDefinition) -> FormatNode:
    return _convert_topcoder_node(definition.return_type, 'ans')


def _convert_topcoder_var_decls(type_: TopcoderType, name: str) -> List[VarDecl]:
    type_table = {
        TopcoderType.Int: (VarType.IndexInt, False),
        TopcoderType.Long: (VarType.ValueInt, False),
        TopcoderType.Double: (VarType.Float, False),
        TopcoderType.String: (VarType.String, False),
        TopcoderType.IntList: (VarType.IndexInt, True),
        TopcoderType.LongList: (VarType.ValueInt, True),
        TopcoderType.DoubleList: (VarType.Float, True),
        TopcoderType.StringList: (VarType.String, True),
    }
    type__, is_list = type_table[type_]
    if is_list:
        length_name = name + '_length'
        return [VarDecl(
            name=length_name,
            type=VarType.IndexInt,
            dims=[],
            bases=[],
            depending=set(),
        ), VarDecl(
            name=name,
            type=type__,
            dims=[length_name],
            bases=['0'],
            depending=set([length_name]),
        )]
    else:
        return [VarDecl(
            name=name,
            type=type__,
            dims=[],
            bases=[],
            depending=set(),
        )]


def convert_topcoder_class_definition_to_input_variables(definition: TopcoderClassDefinition) -> Dict[str, VarDecl]:
    decls = []
    for type_, name in definition.formal_arguments:
        decls.extend(_convert_topcoder_var_decls(type_, name))
    return {decl.name: decl for decl in decls}


def convert_topcoder_class_definition_to_output_variables(definition: TopcoderClassDefinition) -> Dict[str, VarDecl]:
    decls = _convert_topcoder_var_decls(definition.return_type, 'ans')
    return {decl.name: decl for decl in decls}
