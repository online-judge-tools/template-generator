import unittest

import onlinejudge_template.analyzer.constants as analyzer
from onlinejudge_template.network import download_html
from onlinejudge_template.types import *


class TestConstantsDetectorYukicoder(unittest.TestCase):
    """TestConstantsDetectorYukicoder is a class for unit tests about the constants detection of yukicoder (with network access).
    """
    def test_no_1039(self) -> None:
        url = 'https://yukicoder.me/problems/no/1039'
        expected = {
            "MOD": ConstantDecl(name="MOD", value="1000000007", type=VarType.ValueInt),
        }

        html = download_html(url)
        self.assertEqual(analyzer.list_constants_from_html(html), expected)

    def test_no_1073(self) -> None:
        url = 'https://yukicoder.me/problems/no/1073'
        expected = {
            "MOD": ConstantDecl(name="MOD", value="1000000007", type=VarType.ValueInt),
        }

        html = download_html(url)
        self.assertEqual(analyzer.list_constants_from_html(html), expected)
