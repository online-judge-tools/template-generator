# 競プロでの入力受け取る部分を自動生成するやつ

実験的な試み。上手くいったらかなり便利なはず。

## 現状

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

## requirements

``` sh
$ pip3 install requests
$ pip3 install beautifulsoup4
$ pip3 install sympy
```
