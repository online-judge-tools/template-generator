import unittest

import onlinejudge_template.analyzer.constants as analyzer
from onlinejudge_template.network import download_html, download_sample_cases
from onlinejudge_template.types import *


class TestConstantsDetectorAtCoder(unittest.TestCase):
    """TestConstantsDetectorAtCoder is a class for unit tests about the constants detection of AtCoder (with network access).
    """
    def test_agc043_c(self) -> None:
        """In the statement, `,` are used as `998,244,353`.
        """
        url = 'https://atcoder.jp/contests/agc043/tasks/agc043_c'
        expected = {
            "MOD": ConstantDecl(name="MOD", value="998244353", type=VarType.ValueInt),
        }

        html = download_html(url)
        self.assertEqual(analyzer.list_constants_from_html(html), expected)


class TestConstantsDetectorCodeforces(unittest.TestCase):
    """TestConstantsDetectorCodeforces is a class for unit tests about the constants detection of Codeforces (with network access).
    """
    def test_1395_a(self) -> None:
        """The answer is `Yes` or `No`.
        """

        url = 'https://codeforces.com/contest/1395/problem/A'
        expected = {
            "YES": ConstantDecl(name="YES", value="Yes", type=VarType.String),
            "NO": ConstantDecl(name="NO", value="No", type=VarType.String),
        }

        sample_cases = download_sample_cases(url)
        self.assertEqual(analyzer.list_constants_from_sample_cases(sample_cases), expected)


class TestConstantsDetectorYukicoder(unittest.TestCase):
    """TestConstantsDetectorYukicoder is a class for unit tests about the constants detection of yukicoder (with network access).
    """
    def test_no_1039(self) -> None:
        """In the statement, specified as 「$\bmod 10^9+7$で答えてください。」
        """

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


class TestConstantsDetectorTopcoder(unittest.TestCase):
    """TestConstantsDetectorTopcoder is a class for unit tests about the constants detection of Topcoder (with network access).
    """
    def test_apple_trees(self) -> None:
        url = 'https://community.topcoder.com/stat?c=problem_statement&pm=11213'
        expected = {
            "MOD": ConstantDecl(name="MOD", value="1000000007", type=VarType.ValueInt),
        }

        html = download_html(url)
        self.assertEqual(analyzer.list_constants_from_html(html), expected)
