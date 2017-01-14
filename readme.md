# 競プロでの入力受け取る部分を自動生成するやつ

実験的な試み。上手くいったらかなり便利なはず。

## 現状

``` c
$ ./a.py --repeat-macro=REPEAT http://yukicoder.me/problems/no/1 | clang-format
int N;
cin >> N;
int C;
cin >> C;
int V;
cin >> V;
REPEAT(i, V - 1 + 1) { cin >> S[i]; }
REPEAT(i, V - 1 + 1) { cin >> T[i]; }
REPEAT(i, V - 1 + 1) { cin >> Y[i]; }
REPEAT(i, V - 1 + 1) { cin >> M[i]; }
```
