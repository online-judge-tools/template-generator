import unittest

import onlinejudge_template.analyzer.combined as analyzer
from onlinejudge_template.types import *


class TestAnalyzerCombined(unittest.TestCase):
    """TestAnalyzerCombinedCodeforces is a class for integration tests about analyzers (without network access).
    """
    def test_output_format_depending_input_format(self) -> None:
        resources = AnalyzerResources(
            url='https://atcoder.jp/contests/arc093/tasks/arc093_a',
            html=b'...skipped...',
            input_format_string='N\r\nA_1 A_2 ... A_N\r\n',
            output_format_string=None,
            sample_cases=[
                SampleCase(input=b'3\n3 5 -1\n', output=b'12\n8\n10\n'),
                SampleCase(input=b'5\n1 1 1 2 0\n', output=b'4\n4\n4\n2\n4\n'),
                SampleCase(input=b'6\n-679 -2409 -3258 3095 -3291 -4462\n', output=b'21630\n21630\n19932\n8924\n21630\n19288\n'),
            ],
        )

        input_format = SequenceNode(items=[
            ItemNode(indices=[], name='N'),
            NewlineNode(),
            LoopNode(body=ItemNode(indices=['i + 1'], name='A'), name='i', size='N'),
            NewlineNode(),
        ])
        output_format = LoopNode(body=SequenceNode(items=[
            ItemNode(indices=['i'], name='ans'),
            NewlineNode(),
        ]), name='i', size='N')

        analyzed = analyzer.run(resources)
        self.assertEqual(str(analyzed.input_format), str(input_format))
        self.assertEqual(str(analyzed.output_format), str(output_format))
