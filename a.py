#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import bs4
import requests
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

def tokenize(tag):
    it = []
    for y, line in enumerate(tag.find('pre').string.splitlines()):
        line = line.replace('$', '').replace('\\(', '').replace('\\)', '').replace('\\ ', ' ')
        it += [ [] ]
        for x, s in enumerate(line.split()):
            if s == '\\dots':
                it[-1] += [ ('dots', ['hr', 'vr'][x == 0]) ]
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
                    it += [ ('loop', '{}-{}+1'.format(env[name]['r'], env[name]['l']), [  ('read-indexed', '{}'.format(name), 0) ]) ]
                    used.add(name)
                elif item[1] == 'vr':
                    raise NotImplementedError
                else:
                    assert False
            else:
                assert False
    return it

def export(it):
    s = ''
    nest = 0
    def f(it):
        nonlocal s
        nonlocal nest
        if it[0] == 'decl':
            s += '{} {}; '.format(it[1], it[2])
        elif it[0] == 'read':
            s += 'cin >> {};\n'.format(it[1])
        elif it[0] == 'read-indexed':
            s += 'cin >> {}[{}];\n'.format(it[1], 'ijk'[nest - it[2] - 1])
        elif it[0] == 'loop':
            s += 'repeat ({},{}) {}\n'.format('ijk'[nest], it[1], '{')
            nest += 1
            for line in it[2]:
                f(line)
            nest -= 1
            s += '}\n'
        else:
            assert False
    for line in it:
        f(line)
    return s

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    args = parser.parse_args()

    resp = requests.get(args.url)
    soup = bs4.BeautifulSoup(resp.content.decode(resp.encoding), 'html.parser')

    for h4 in soup.find_all('h4'):
        if h4.string == '入力':
            it = tokenize(h4.parent)
            it = parse(it)
            print(export(it))

