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

TODO: 書く


## Detailed Design

TODO: 書く。なお、動作原理の簡単な説明は [how-it-works.html](https://online-judge-template-generator.readthedocs.io/en/latest/) にある (これはそのうち消えるかも)。個別の機能については modules 冒頭の docstring にも説明がある。


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
