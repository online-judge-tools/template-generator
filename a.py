#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import bs4
import requests
import sympy
import sympy.parsing.sympy_parser
import argparse
import collections
import copy

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
                if ix.startswith('{') and ix.endswith('}'):
                    ix = ix[1:-1]
                if ',' in ix:
                    raise NotImplementedError
                it[-1] += [ ('indexed', s, ix) ]
            else:
                it[-1] += [ ('fixed', s) ]
    return it

def merge(xs):
    ys = []
    for x in xs:
        if ys and ys[-1][0] == x[0] and x[0] in [ 'decl', 'decl-vector' ] and ys[-1][1] == x[1]:
            ys[-1] = list(ys[-1])
            ys[-1][2] += x[2]
            ys[-1] = tuple(ys[-1])
        elif ys and ys[-1][0] == x[0] and x[0] in [ 'read', 'read-indexed' ]:
            ys[-1] = list(ys[-1])
            ys[-1][1] += x[1]
            ys[-1] = tuple(ys[-1])
        else:
            ys += [ x ]
    return ys

def simplify(s):
    local_dict = { 'N': sympy.Symbol('N') }
    return str( sympy.parsing.sympy_parser.parse_expr( s, local_dict=local_dict ))

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
    for name in env:
        env[name]['n'] = simplify('{}-{}+1'.format(env[name]['r'], env[name]['l']))
    it = []
    used = set()
    for y, line in enumerate(tokens):
        for x, item in enumerate(line):
            decls = []
            reads = []
            if item[0] == 'fixed':
                decls += [ ('decl', 'int', [ item[1] ]) ]
                reads += [ ('read', [ item[1] ]) ]
            elif item[0] == 'indexed':
                pass
            elif item[0] == 'dots':
                it += merge(decls) + merge(reads)
                decls = []
                reads = []
                if item[1] == 'hr':
                    assert line[x-1][0] == 'indexed'
                    name = line[x-1][1]
                    if name in used:
                        continue
                    n = env[name]['n']
                    it += [ ('decl-vector', 'int', [ (name, n) ]) ]
                    it += [ ('loop', n, [ ('read-indexed', [ (name, 0) ]) ]) ]
                    used.add(name)
                elif item[1] == 'vr':
                    names = []
                    for item in tokens[y-1]:
                        if item[0] != 'indexed':
                            raise NotImplementedError
                        name = item[1]
                        if name in used:
                            continue
                        names += [ name ]
                        used.add(name)
                    if not names:
                        continue
                    acc = []
                    n = env[names[0]]['n']
                    for name in names:
                        assert env[name]['n'] == n
                        decls  += [ ('decl-vector', 'int', [ (name, n) ]) ]
                        reads += [ ('read-indexed', [ (name, 0) ]) ]
                    it += merge(decls)
                    it += [ ('loop', n, merge(reads)) ]
                    decls = []
                    reads = []
                else:
                    assert False
            else:
                assert False
            it += merge(decls) + merge(reads)
    return it

def paren_if(n, lr):
    if n:
        return lr[0] + n + lr[1]
    else:
        return n

def export(it, repeat_macro=None):
    def go(it, nest):
        if it[0] == 'decl':
            if it[2]:
                return '{} {}; '.format(it[1], ', '.join(it[2]))
        elif it[0] == 'decl-vector':
            if it[2]:
                return 'vector<{}> {}; '.format(it[1], ', '.join(map(lambda x: x[0] + paren_if(x[1], '()'), it[2])))
        elif it[0] == 'read':
            return 'cin >> {};\n'.format(' >> '.join(it[1]))
        elif it[0] == 'read-indexed':
            return 'cin >> {};\n'.format(' >> '.join(map(lambda x: x[0] + '[' + 'ijk'[nest - x[1] - 1] + ']', it[1])))
        elif it[0] == 'loop':
            s = ''
            i = 'ijk'[nest]
            if repeat_macro is None:
                s += 'for (int {} = 0; {} < {}; ++ {}) '.format(i, i, it[1], i)
            else:
                s += '{} ({},{}) '.format(repeat_macro, i, it[1])
            if len(it[2]) == 0:
                s += ';'
            elif len(it[2]) == 1:
                s += go(it[2][0], nest+1)
            else:
                s += '{ '
                for line in it[2]:
                    s += go(line, nest+1).rstrip() + ' '
                s += '}\n'
            return s
        else:
            assert False
    s = ''
    for line in it:
        s += go(line, 0)
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
