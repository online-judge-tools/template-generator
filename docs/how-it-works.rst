How it works (Japanese) / どのようにして動いているのか (日本語)
============================================================

たとえば Library Checker の問題 [Static RQM](https://judge.yosupo.jp/problem/staticrmq) について考えてみましょう。
この問題の入力フォーマットは次のようになっています。
::

    n m
    a₀ a₁ … aₙ₋₁
    l₁ r₁
    ⋮
    lₘ rₘ

これをまず以下のようなトークン列に分解します。
愚直に貪欲をするだけで、やばい規則もないのでほぼ O(n) です。正規表現で便利に書ける既存のツールがあるのでこれを利用しています。

.. code-block:: json

    [
        "ident(n)", "ident(m)", "newline()",
        "ident(a)", "subscript()", "number(0)", "ident(a)", "subscript()", "number(1)", "dots()", "ident(a)", "subscript()", "ident(n)", "binop(-)", "number(1)", "newline()",
        "ident(l)", "subscript()", "number(1)", "ident(r)", "subscript()", "number(1)", "newline()",
        "vdots(1)", "newline()",
        "ident(l)", "subscript()", "ident(m)", "ident(r)", "subscript()", "ident(m)", "newline()"
    ]

このトークン列を解析して次のような木へ変形します。
まず文脈自由文法で解析できる範囲を処理して木を作った後に、文脈依存ぽい部分を ad-hoc に処理してより整理された木に組み換えています。
文脈自由部分は O(n^3) の愚直な区間 DP (CYK法) でもよいですが、規則を列挙すれば残りをいい感じにやってくれる既存のツール (Yacc) に任せてほぼ線形 (LALR法) で実装されています。

.. code-block:: json
    [
        {"type": "var", "name": "n"},
        {"type": "var", "name": "m"},
        {"type": "newline"},
        {"type": "loop", "counter": "i", "size": "n", "body": [
            {"type": "var", "name": "a", "subscript": "i"}
        ]},
        {"type": "newline"},
        {"type": "loop", "counter": "j", "size": "m", "body": [
            {"type": "var", "name": "l", "subscript": "j + 1"},
            {"type": "var", "name": "r", "subscript": "j + 1"},
            {"type": "newline"}
        ]}
    ]

この木を変換してソースコードにします。
木の畳み込みとか木 DP とか言われる O(n) か O(n²) ぐらいの愚直をします。
何をやっても変換はできますが、(1.) まずフォーマット木を C++ の構文木に写し、(2.) それを最適化し、(3.) これを行の列に直列化し、(4.) インデントを整えて出力する、という 4 段階に分けると実装が楽かつ出力がきれいです。

.. code-block:: c++

    int n, m;
    scanf("%d%d", &n, &m);
    std::vector<int> a(n);
    for (int i = 0; i < n; ++i) {
        scanf("%d", &a[i]);
    }
    std::vector<int> l(m), r(m);
    for (int j = 0; j < m; ++j) {
        scanf("%d%d", &l[j], &r[j]);
    }

この一連の作業をよろしくやってくれるのがこのツールです。
