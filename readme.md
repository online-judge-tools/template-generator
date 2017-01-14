# 競プロでの入力受け取る部分を自動生成するやつ

実験的な試み。上手くいったらかなり便利なはず。

制約を読んで値の範囲等の情報を取るのはしんどそうなので誰か頼むという気持ち。

## 現状

できた:

-   固定
    -   例: http://yukicoder.me/problems/no/6
-   横
    -   例: http://yukicoder.me/problems/no/12
-   縦
    -   例: http://yukicoder.me/problems/no/8

まだ:

-   2次元
    -   例: http://yukicoder.me/problems/no/20
-   グラフをいい感じにする
    -   例: http://yukicoder.me/problems/no/317
    -   引数で指定とかしないとだめそう
-   `scanf`対応

たぶんやらない:
-   C++以外の言語の対応
-   `int`以外
    -   例: http://yukicoder.me/problems/no/18
-   複雑な演算
    -   例: http://yukicoder.me/problems/no/66
-   固定文字列
    -   例: http://yukicoder.me/problems/no/70
-   複雑な添字
    -   例: http://yukicoder.me/problems/no/73

## example

``` c
$ ./a.py --repeat-macro=REPEAT http://yukicoder.me/problems/no/1
int N; cin >> N;
int C; cin >> C;
int V; cin >> V;
vector<int> S(V); REPEAT (i,V) cin >> S[i];
vector<int> T(V); REPEAT (i,V) cin >> T[i];
vector<int> Y(V); REPEAT (i,V) cin >> Y[i];
vector<int> M(V); REPEAT (i,V) cin >> M[i];
```

``` c
$ ./a.py http://yukicoder.me/problems/no/8
int P; cin >> P;
vector<int> N(P), K(P); for (int i = 0; i < P; ++ i) cin >> N[i] >> K[i];
```

## requirements

``` sh
$ pip3 install requests
$ pip3 install beautifulsoup4
$ pip3 install sympy
```
