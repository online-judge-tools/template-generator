# Design Doc

link: [DESIGN.md](https://github.com/online-judge-tools/.github/blob/master/DESIGN.md) of [online-judge-tools](https://github.com/online-judge-tools) organization


## Objective

`oj-template` コマンドは、競技プログラミングの問題を解析しテンプレートコードを生成する。
特に、問題に依存した入出力パートやランダムケース生成器の自動生成をする。

また `oj-prepare` コマンドは、多数回の `oj-template` コマンドの実行を補助する。これは同時にコンテスト一括でサンプルケースを取得機能も提供する。


## Goals

-   入出力パートなどの問題に依存したボイラープレートの生成
-   ランダムケース生成の効率化


## Non-Goals

-   問題の解法コードそのものの生成


## Background

競技プログラミングの解法コードのパラメタの受け渡しには、標準入出力を通した空白区切りのテキストを用いるのが慣習である。
JSON や Protocol Buffers などは用いられない。
そのフォーマットは自然言語ないし簡単な図示により指定される。
所定のメソッドを持つクラスを含むコードを提出する形式もまれに見られるが、対応言語数が制限されてしまうことからこれは主流ではない。
通常は問題ごとに `printf` や `scanf` を用いて手で入出力を記述する必要があった。


## Overview

### format tree

多くの中心となる中間表現は「フォーマット木」と呼ばれるもので、Haskell 風に書くと以下のようなものである。

``` haskell
data FormatNode
    = ItemNode { name :: VarName, index :: [Expr] }
    | NewlineNode
    | LoopNode { counter :: VarName, count :: Expr, body :: FormatNode }
    | SequenceNode { body :: [FormatNode] }
```

たとえば、

```
N M
A_0 A_1 ... A_{N-1}
X_0 Y_0
X_1 Y_1
...
X_{M-1} Y_{M-1}
```

などと表現される入力フォーマットには、

```
SequenceNode
    [ ItemNode "N" []
    , ItemNode "M" []
    , NewlineNode
    , LoopNode "i" "N" $
        ItemNode "A" ["i"]
    , NewlineNode
    , LoopNode "j" "M" $ SequenceNode
        [ ItemNode "X" ["j"]
        , ItemNode "Y" ["j"]
        , NewlineNode
        ]
    ]
```

というフォーマット木が対応する。


### code structure

内部は大きく以下のふたつの部分に分けられている。

1.  問題の解析をする部分  (`onlinejudge_template/analyzer/`)
    -   サンプルケースの取得  ([online-judge-tools/api-client](https://github.com/online-judge-tools/api-client) を利用)
    -   入出力フォーマットを表現する `<pre>` の取得と解析  (Lex および Yacc による古典的手法を利用)
    -   サンプルケースからの入出力フォーマットの推測
    -   入出力フォーマットに含まれる変数の型の推測  (Hindley-Milner 型推論を参考にした実装を利用)
    -   MOD や YES / NO などの定数の解析
1.  解析結果を使ってコードを生成する部分  (`onlinejudge_template/generator/`)
    -   フォーマット木を言語ごとの抽象構文木に変換
    -   具体的なコードの生成  ([Mako](https://www.makotemplates.org/) を利用)
    -   後処理としてのコードの整形  ([clang-format](https://clang.llvm.org/docs/ClangFormat.html) や [yapf](https://github.com/google/yapf) を利用)

なお、動作原理の簡単な説明は [how-it-works.html](https://online-judge-template-generator.readthedocs.io/en/latest/) にある (これはそのうち消えるかも)。
個別の機能については modules 冒頭の docstring にも説明がある。


## Detailed Design

-   できる限り説明性のよい手法での解析をするようにする。「この問題の解析は成功しますか？」という問いに「実際に実行してみれば分かります」と答えるしかない状況や「この問題の解析が成功/失敗したのはなぜですか？」という問いに「たまたまそういう実装だったからです」と答えるしかない状況は可能ならば避けたい。
-   本質は入出力部分の生成であるが、その他の部分も出力しコンパイル可能なファイルの全体を生成するのは重要だろう。
-   入出力部分の生成のみに注力し、それ以外は外部ツールに移譲する。入出力部分以外は Mako テンプレートとしてユーザによるカスタマイズが可能にしておく。また整形は外部のフォーマッタを利用する。これは開発者にとってのコストの低減およびユーザにとっての柔軟性の増加というふたつの効果を持つ。
-   `oj-prepare` コマンドは「利便性でユーザを釣る」そして「`generate.py` という重要だが多くのユーザが気付かないファイルを強制的に認識させる」手段として用意されている。


## Security Considerations

特になし。
内部で利用している [online-judge-tools/api-client](https://github.com/online-judge-tools/api-client) の問題は継承する。


## Privacy Considerations

特になし。


## Metrics Considerations

PePy <https://pepy.tech/project/online-judge-template-generator> を見るとユーザ数の概算が得られる。
生成されたテンプレートに埋め込まれた banner をオンラインジャッジへの提出結果から見付けて数えることもできるが、これを自動化する機構はまだない。
個別の機能の利用状況についての統計は得られない。

2020/09/20 時点では、ユーザはおよそ 200 人から 300 人程度だろう。
バージョン更新通知の機構がなく、古いバージョンを使い続けているユーザが多いだろうことにも注意したい。


## Testing Plan

TODO: 書く
