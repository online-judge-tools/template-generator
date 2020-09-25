import unittest

import onlinejudge_template.analyzer.topcoder as analyzer
from onlinejudge_template.network import download_html
from onlinejudge_template.types import *


class TestFormatStringDetectorTopcoder(unittest.TestCase):
    """TestFormatStringAnalyzerTopcoder is a class for unit tests for the parser of the class specification of Topcoder (with network access).
    """
    def test_10760(self):
        # `double` is used and one of values is a scientific form `1.0E50`.
        url = 'https://community.topcoder.com/stat?c=problem_statement&pm=10760'
        expected = TopcoderClassDefinition(
            class_name='Nisoku',
            method_name='theMax',
            formal_arguments=[(TopcoderType.DoubleList, 'cards')],
            return_type=TopcoderType.Double,
        )

        html = download_html(url)
        definition = analyzer.parse_topcoder_class_definition(html, url=url)
        self.assertEqual(definition, expected)

    def test_11026(self):
        # `String[]` is used.
        # The type of the return value is a list.
        url = 'https://community.topcoder.com/stat?c=problem_statement&pm=11026'
        expected = TopcoderClassDefinition(
            class_name='RandomApple',
            method_name='theProbability',
            formal_arguments=[(TopcoderType.StringList, 'hundred'), (TopcoderType.StringList, 'ten'), (TopcoderType.StringList, 'one')],
            return_type=TopcoderType.DoubleList,
        )

        html = download_html(url)
        definition = analyzer.parse_topcoder_class_definition(html, url=url)
        self.assertEqual(definition, expected)

    # TODO: This problem may be deleted (found at 2020/09/19). Wait for a while (a month?) and delete this test if the problem actually deleted.
    @unittest.expectedFailure
    def test_10727(self):
        # `long` is used.
        url = 'https://community.topcoder.com/stat?c=problem_statement&pm=10727'
        expected = TopcoderClassDefinition(
            class_name='RabbitPuzzle',
            method_name='theCount',
            formal_arguments=[(TopcoderType.LongList, 'rabbits'), (TopcoderType.LongList, 'nests'), (TopcoderType.Int, 'K')],
            return_type=TopcoderType.Int,
        )

        html = download_html(url)
        definition = analyzer.parse_topcoder_class_definition(html, url=url)
        self.assertEqual(definition, expected)
