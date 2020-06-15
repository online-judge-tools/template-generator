import unittest

import onlinejudge_template.analyzer.html as analyzer
from onlinejudge_template.network import download_html


class TestFormatStringDetectorAtCoder(unittest.TestCase):
    """TestFormatStringDetectorAtCoder is a class for unit tests about the format string detection of AtCoder (with network access).
    """
    def test_agc041_a(self) -> None:
        url = 'https://atcoder.jp/contests/agc041/tasks/agc041_a'
        expected = '\r\n'.join([
            r'<var>N</var> <var>A</var> <var>B</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_agc041_b(self) -> None:
        url = 'https://atcoder.jp/contests/agc041/tasks/agc041_b'
        expected = '\r\n'.join([
            r'<var>N</var> <var>M</var> <var>V</var> <var>P</var>',
            r'<var>A_1</var> <var>A_2</var> <var>...</var> <var>A_N</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_abc080_a(self) -> None:
        url = 'https://atcoder.jp/contests/abc080/tasks/abc080_a'
        expected = '\r\n'.join([
            r'<var>N</var> <var>A</var> <var>B</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_abc042_a(self) -> None:
        url = 'https://atcoder.jp/contests/abc042/tasks/abc042_a'
        expected = '\r\n'.join([
            r'<var>A</var> <var>B</var> <var>C</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    @unittest.expectedFailure
    def test_arc001_1(self) -> None:
        url = 'https://atcoder.jp/contests/arc001/tasks/arc001_1'
        expected = '\r\n'.join([
            r'',
            r'<var>N</var>',
            r'<var>c_1c_2c_3…c_N</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    @unittest.expectedFailure
    def test_arc001_3(self) -> None:
        url = 'https://atcoder.jp/contests/arc001/tasks/arc001_3'
        expected = '\r\n'.join([
            r'',
            r'<var>c_{11}</var> <var>c_{12}</var> … <var>c_{18}</var>',
            r'<var>c_{21}</var> <var>c_{22}</var> … <var>c_{28}</var>',
            r':',
            r':',
            r'<var>c_{81}</var> <var>c_{82}</var> … <var>c_{88}</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    @unittest.expectedFailure
    def test_arc001_4(self) -> None:
        url = 'https://atcoder.jp/contests/arc001/tasks/arc001_4'
        expected = '\r\n'.join([
            r'',
            r'<var>N</var>',
            r'<var>start</var> <var>goal</var>',
            r'<var>l_0</var> <var>r_0</var>',
            r'<var>l_1</var> <var>r_1</var>',
            r'<var>:</var>',
            r'<var>:</var>',
            r'<var>l_N</var> <var>r_N</var>',
            r'',
        ]).replace('<var>', '').replace('</var>', '').strip() + '\r\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))


class TestFormatStringDetectorLibraryChecker(unittest.TestCase):
    """TestFormatStringDetectorLibraryChecker is a class for unit tests about the format string detection of Library Checker (with network access).
    """
    def test_unionfind(self) -> None:
        url = 'https://judge.yosupo.jp/problem/unionfind'
        expected = '\n'.join([
            r'$N$ $Q$',
            r'$t_1$ $u_1$ $v_1$',
            r'$t_2$ $u_2$ $v_2$',
            r':',
            r'$t_Q$ $u_Q$ $v_Q$',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_two_edge_connected_components(self) -> None:
        url = 'https://judge.yosupo.jp/problem/two_edge_connected_components'
        expected_input = '\n'.join([
            r'$N$ $M$',
            r'$a_0$ $b_0$',
            r'$a_1$ $b_1$',
            r':',
            r'$a_{M - 1}$ $b_{M - 1}$',
            r'',
        ]).strip() + '\n'
        expected_output = '\n'.join([
            r'$l$ $v_0$ $v_1$ ... $v_{l-1}$',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected_input)
        self.assertEqual(analyzer.parse_output_format_string(html, url=url), expected_output)

    def test_stirling_number_of_the_second_kind(self) -> None:
        url = 'https://judge.yosupo.jp/problem/stirling_number_of_the_second_kind'
        expected_input = '\n'.join([
            r'$N$',
            r'',
        ]).strip() + '\n'
        expected_output = '\n'.join([
            r'$S(N, 0)$ $\cdots$ $S(N, N)$',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected_input)
        self.assertEqual(analyzer.parse_output_format_string(html, url=url), expected_output)


class TestFormatStringDetectorYukicoder(unittest.TestCase):
    """TestFormatStringDetectorYukicoder is a class for unit tests about the format string detection of yukicoder (with network access).
    """
    def test_no_1000(self) -> None:
        url = 'https://yukicoder.me/problems/no/1000'
        expected = '\n'.join([
            r'$N\ Q$',
            r'$A_1\ A_2\ \cdots \ A_N$',
            r'$c_1\ x_1\ y_1$',
            r'$c_2\ x_2\ y_2$',
            r'$\vdots$',
            r'$c_Q\ x_Q\ y_Q$',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_no_999(self) -> None:
        url = 'https://yukicoder.me/problems/no/999'
        expected = '\n'.join([
            r'$N$',
            r'$A_1\ A_2\ \cdots \ A_{2N}$',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_no_100(self) -> None:
        url = 'https://yukicoder.me/problems/no/100'
        expected = '\n'.join([
            r'$N$',
            r'$a_1$ $\ldots$ $a_N$',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))

    def test_no_1(self) -> None:
        url = 'https://yukicoder.me/problems/no/1'
        expected = '\n'.join([
            r'\(N\)',
            r'\(C\)',
            r'\(V\)',
            r'\(S_1\ S_2\ S_3\ \dots\ S_V\)',
            r'\(T_1\ T_2\ T_3\ \dots\ T_V\)',
            r'\(Y_1\ Y_2\ Y_3\ \dots\ Y_V\)',
            r'\(M_1\ M_2\ M_3\ \dots\ M_V\)',
            r'',
        ]).strip() + '\n'

        html = download_html(url)
        self.assertEqual(analyzer.parse_input_format_string(html, url=url), expected)
        self.assertRaises(analyzer.HTMLParserError, lambda: analyzer.parse_output_format_string(html, url=url))
