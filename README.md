# online-judge-tools/template-generator

[![test](https://github.com/kmyk/online-judge-template-generator/workflows/test/badge.svg)](https://github.com/kmyk/online-judge-template-generator/actions)
[![Documentation Status](https://readthedocs.org/projects/online-judge-template-generator/badge/)](https://online-judge-template-generator.readthedocs.io/en/latest/)
[![PyPI](https://img.shields.io/pypi/v/online-judge-template-generator)](https://pypi.org/project/online-judge-template-generator/)
[![LICENSE](https://img.shields.io/pypi/l/online-judge-template-generator.svg)](https://github.com/kmyk/online-judge-template-generator/blob/master/LICENSE)

[README 日本語バージョン](https://github.com/online-judge-tools/template-generator/blob/master/README.ja.md)


## What is this


This tool analyzes problems and generates template codes for competitive programming.

Online Demo: <https://online-judge-tools.github.io/template-generator-webapp/>


## How to install

``` console
$ pip3 install online-judge-template-generator
```


## Usage

`oj-template` command analyzes the specified problem and generates the template files (e.g. `main.cpp`) including input/output part (e.g. `int n; std::cin >> n;`) and the generators (e.g. `generate.py`) of random test cases for the problem. See [Examples](#examples).
This works on many online judges which [`oj` command](https://github.com/kmyk/online-judge-tools) works.

``` console
$ oj-template [-t TEMPLATE] URL
```

`oj-prepare` command prepares some template files and test cases for a problem or a contest at once. This is a thin wrapper of `oj` command and `oj-template` command.
This works on many online judges which [`oj` command](https://github.com/kmyk/online-judge-tools) works.

``` console
$ oj-prepare URL
```


### Supported languages

The following template files are prepared as builtin of `oj-template` command.

-   `main.cpp`: solution in C++
-   `main.py`: solution in Python
-   `generate.py`: random case generator in Python
-   `generate.cpp`: random case generator in C++

The builtin templates invoke [`clang-format` command](https://clang.llvm.org/docs/ClangFormat.html) and [`yapf` command](https://github.com/google/yapf) when they exist.
Please install them too if you want to generate better formatted code.


### Generating random cases

To generate random cases, please run `oj-prepare https://...` command, edit the generated `generate.py` file, and run the following command:

``` console
$ oj generate-input "python3 generate.py"
```

You can also generate the file `generate.py` with the running the command `oj-template -t generate.py "https://..."`.


## Examples

``` console
$ oj-template https://codeforces.com/contest/1300/problem/D
...

#include <bits/stdc++.h>
#define REP(i, n) for (int i = 0; (i) < (int)(n); ++ (i))
#define REP3(i, m, n) for (int i = (m); (i) < (int)(n); ++ (i))
#define REP_R(i, n) for (int i = (int)(n) - 1; (i) >= 0; -- (i))
#define REP3R(i, m, n) for (int i = (int)(n) - 1; (i) >= (int)(m); -- (i))
#define ALL(x) ::std::begin(x), ::std::end(x)
using namespace std;

const string YES = "YES";
const string NO = "nO";
bool solve(int n, const vector<int64_t> & a, const vector<int64_t> & b) {
    // TODO: edit here
}

// generated by online-judge-template-generator v4.4.0 (https://github.com/kmyk/online-judge-template-generator)
int main() {
    std::ios::sync_with_stdio(false);
    std::cin.tie(nullptr);
    constexpr char endl = '\n';
    int n;
    cin >> n;
    vector<int64_t> a(n), b(n);
    REP (i, n) {
        cin >> a[i] >> b[i];
    }
    auto ans = solve(n, a, b);
    cout << (ans ? YES : NO) << endl;
    return 0;
}
```

``` console
$ oj-template -t generate.py https://judge.yosupo.jp/problem/staticrmq
...

#!/usr/bin/env python3
import random
import onlinejudge_random as random_oj

def main():
    N = random.randint(1, 10 ** 9)  # TODO: edit here
    a = [None for _ in range(N)]
    Q = random.randint(1, 10 ** 9)  # TODO: edit here
    l = [None for _ in range(Q)]
    r = [None for _ in range(Q)]
    for i in range(N):
        a[i] = random.randint(1, 10 ** 9)  # TODO: edit here
    for i in range(Q):
        l[i] = random.randint(1, 10 ** 9)  # TODO: edit here
        r[i] = random.randint(1, 10 ** 9)  # TODO: edit here
    print(N, Q)
    print(*[a[i] for i in range(N)])
    for i in range(Q):
        print(l[i], r[i])

if __name__ == "__main__":
    main()
```

``` console
$ oj-prepare https://atcoder.jp/contests/abc158
...

$ tree
.
├── abc158_a
│   ├── main.cpp
│   ├── main.py
│   ├── generate.py
│   └── test
│       ├── sample-1.in
│       ├── sample-1.in
│       ├── sample-1.out
│       ├── sample-2.in
│       ├── sample-2.out
│       ├── sample-3.in
│       └── sample-3.out
├── ...
├── ...
├── ...
├── ...
└── abc158_f
    ├── main.cpp
    ├── main.py
    ├── generate.py
    └── test
        ├── sample-1.in
        ├── sample-1.out
        ├── sample-2.in
        ├── sample-2.out
        ├── sample-3.in
        ├── sample-3.out
        ├── sample-4.in
        └── sample-4.out

13 directories, 50 files
```


## Settings

### oj-template

The template file for `oj-template` command can be specified with the `-t` option.
You can see the list of builtin template files at [onlinejudge_template_resources/template/](https://github.com/online-judge-tools/template-generator/tree/master/onlinejudge_template_resources/template).
For example, if you want to use [generate.cpp](https://github.com/online-judge-tools/template-generator/blob/master/onlinejudge_template_resources/template/generate.cpp), please run as `oj-template -t generate.cpp https://...`.

You can make a new template by yourself.
The format of template files is [Mako](https://www.makotemplates.org/)'s one.
Please write by reference to existing files like
[fastio_sample.cpp](https://github.com/kmyk/online-judge-template-generator/blob/master/onlinejudge_template_resources/template/fastio_sample.cpp) or [customize_sample.cpp](https://github.com/kmyk/online-judge-template-generator/blob/master/onlinejudge_template_resources/template/customize_sample.cpp)>
API documentation exists at [onlinejudge_template.generator package](https://online-judge-template-generator.readthedocs.io/en/latest/onlinejudge_template.generator.html).

To specify your new template file with `-t` option, please include the path separator character `/` in the given path (this is similar to the behavior of executing a command out of PATH in shell).
For example, if you write a template file named `customized.py`, please run `oj-template -t ./customized.py https://...` or `oj-template -t /path/to/customized.py https://...`.
Also you can use certain directory (when you use Linux, it's `~/.config/online-judge-tools/template/`) to place template files like `~/.config/online-judge-tools/template/customized.py`. If templates exist in this directory, you can specify them as `oj-template -t customized.py https://...`. If templates files whose names are the same to builtin templates, they are override the builtin files.

### oj-prepare

The config file for `oj-prepare` can be found at the following paths depending on your operating system:
`~/.config/online-judge-tools/prepare.config.toml` (Linux)
`/Users/{user_name}/Library/Application Support/online-judge-tools/prepare.config.toml` (MacOS)

Please use the following format when editing the file:

``` toml
contest_directory = "~/Desktop/{service_domain}/{contest_id}/{problem_id}"
problem_directory = "."

[templates]
"main.py" = "main.py"
"naive.py" = "main.py"
"generate.py" = "generate.py"
```

Available items:

-   `problem_directory` (string): When a URL of a problem is given to the command, use `{problem_directory}` for the directory.
    -   default: `.`
    -   available vairables:
        -   `{problem_id}`: problem ID (e.g. `abc123_d`)
-   `contest_directory` (string): When a URL of a contest is given to the command, use `{contest_directory}/{problem_directory}` for the directory.
    -   default: `{problem_id}`
    -   available vairables:
        -   `{problem_id}`: problem ID (e.g. `abc123_d`)
        -   `{contest_id}`: contest ID (e.g. `abc123`)
        -   `{service_domain}`: the domain of the online judge (e.g. `codeforces.com`)
        -   `{service_name}`: the name of the online judge (e.g. `Codeforces`)
-   `templates` (table of string): places the generated code specified by value (the right of `=`) into paths specified by key (the left of `=`).
    -   example: `{ "solution.cpp" = "main.cpp", "naive.py" = main.py", "generate.cpp" = "generate.cpp" }`
    -   default: `{ "main.cpp" = "main.cpp", "main.py" = "main.py", "generate.py" = "generate.py" }`


## License

MIT License
