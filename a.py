#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import bs4
import requests
import sympy
import sympy.parsing.sympy_parser
import argparse
import collections
import copy

# samples
# http://yukicoder.me/problems/no/1
# http://yukicoder.me/problems/no/2   # N
# http://yukicoder.me/problems/no/6   # N K
# http://yukicoder.me/problems/no/8   # vertical
# http://yukicoder.me/problems/no/17  # S_{N-1}
# http://yukicoder.me/problems/no/20  # 2D
# http://yukicoder.me/problems/no/13  # 2D (hard)
# http://yukicoder.me/problems/no/12  # A_1 \dots A_i \dots A_N
# http://yukicoder.me/problems/no/11  # A_1 \dots A_i \dots A_N (vertical)
# http://yukicoder.me/problems/no/18  # string
# http://yukicoder.me/problems/no/66  # S_{2^M}
# http://yukicoder.me/problems/no/70  # :
# http://yukicoder.me/problems/no/73  # C_a \dots C_z

def scrape(url):
    resp = requests.get(url)
    soup = bs4.BeautifulSoup(resp.content.decode(resp.encoding), 'html.parser')
    if 'yukicoder.me' in url:
        for h4 in soup.find_all('h4'):
            if h4.string == '入力':
                return h4.parent.find('pre').string
    elif 'atcoder.jp' in url:
        for h3 in soup.find_all('h3'):
            if h3.string == '入力':
                s = ''
                for it in h3.parent.find('pre'):
                    s += it.string or it
                return s
    else:
        raise NotImplementedError

def tokenize(pre):
    it = []
    for y, line in enumerate(pre.splitlines()):
        line = line.replace('$', '').replace('\\(', '').replace('\\)', '').replace('\\ ', ' ')
        it += [ [] ]
        for x, s in enumerate(line.split()):
            if s == '\\dots':
                it[-1] += [ ('dots', ['hr', 'vr'][x == 0]) ]
            elif s == ':':
                it[-1] += [ ('dots', 'vr') ]
            elif s == '...':
                it[-1] += [ ('dots', 'hr') ]
            elif '\\' in s:
                assert False
            elif '_' in s:
                assert s.count('_') == 1
                s, ix = s.split('_')
                it[-1] += [ ('indexed', s, ix) ]
            else:
                it[-1] += [ ('fixed', s) ]
    return it

def parse(tokens):
    env = collections.defaultdict(dict)
    for y, line in enumerate(tokens):
        for x, item in enumerate(line):
            if item[0] == 'indexed':
                f = env[item[1]]
                if item[2] in 'ijk': # for A_1 \dots A_i \dots A_N
                    continue
                if 'l' not in f or item[2] < f['l']:
                    f['l'] = item[2]
                if 'r' not in f or f['r'] < item[2]:
                    f['r'] = item[2]
    it = []
    used = set()
    for y, line in enumerate(tokens):
        if y+1 < len(tokens) and tokens[y+1][0][0] == 'dots':
            continue
        for x, item in enumerate(line):
            if x+1 < len(line) and line[x+1][0] == 'dots':
                continue
            if item[0] == 'fixed':
                it += [ ('decl', 'int', item[1]), ('read', item[1]) ]
            elif item[0] == 'indexed':
                pass
            elif item[0] == 'dots':
                if item[1] == 'hr':
                    assert line[x-1][0] == 'indexed'
                    name = line[x-1][1]
                    n = str(sympy.expand( sympy.parsing.sympy_parser.parse_expr( '{}-{}+1'.format(env[name]['r'], env[name]['l']))))
                    it += [ ('decl-vector', 'int', name, n), ('loop', n, [  ('read-indexed', name, 0) ]) ]
                    used.add(name)
                elif item[1] == 'vr':
                    raise NotImplementedError
                else:
                    assert False
            else:
                assert False
    return it

def export(it, repeat_macro=None):
    s = ''
    nest = 0
    def f(it):
        nonlocal s
        nonlocal nest
        if it[0] == 'decl':
            s += '{} {}; '.format(it[1], it[2])
        elif it[0] == 'decl-vector':
            s += 'vector<{}> {}({}); '.format(it[1], it[2], it[3])
        elif it[0] == 'read':
            s += 'cin >> {};\n'.format(it[1])
        elif it[0] == 'read-indexed':
            s += 'cin >> {}[{}];\n'.format(it[1], 'ijk'[nest - it[2] - 1])
        elif it[0] == 'loop':
            i = 'ijk'[nest]
            if repeat_macro is None:
                s += 'for (int {} = 0; {} < {}; ++ {}) '.format(i, i, it[1], i)
            else:
                s += '{} ({},{}) '.format(repeat_macro, i, it[1])
            nest += 1
            if len(it[2]) == 0:
                s += ';'
            elif len(it[2]) == 1:
                f(it[2][0])
            else:
                s += '{\n'
                for line in it[2]:
                    f(line)
                s += '}\n'
            nest -= 1
        else:
            assert False
    for line in it:
        f(line)
    return s

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('--repeat-macro')
    args = parser.parse_args()

    it = scrape(args.url)
    it = tokenize(it)
    it = parse(it)
    print(export(it, repeat_macro=args.repeat_macro), end='')


if __name__ == '__main__':
    main()
