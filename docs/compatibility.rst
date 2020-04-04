Compatibility / 互換性について
==============================

The current version ``v2.7.0`` is still unstable.

Stable features (Japanese) / 安定な機能 (日本語)
------------------------------------------------

``oj-template`` コマンドを以下の形式で使うことについては安全です。
::

   $ oj-template [-t TEMPLATE] URL

テンプレートとしては、解法コード用の ``main.cpp`` と ``main.py`` と、ランダムケース生成用の ``generate.py`` が使えます。
また、絶対パスで [Mako](https://www.makotemplates.org/) のテンプレートファイルを指定することもできます。


Unstable features (Japanese) / 不安定な機能 (日本語)
----------------------------------------------------

その他の利用法については、後方互換性を保証しません。つまり、バージョンが上がると動かなくなる可能性があります。

- [Mako](https://www.makotemplates.org/) のテンプレートファイルに与えられるデータの形式は不安定です。もう少し使ってみて様子を見たい。
- ``oj_template`` module や ``oj_random`` module は不安定です。これももう少し使ってみて様子を見たい。
- ``oj-prepare`` コマンドは不安定です。 ``oj2`` のような名前のコマンドとして生まれ変わる可能性や、他のプロジェクトで十分だとして廃止される可能性があります。
- 設定ファイルのパスや内容の形式は不安定です。
