# 競プロで入力受け取る部分を自動生成するやつ

## 現状

``` c
$ ./a.py http://yukicoder.me/problems/no/1 | clang-format
int N;
cin >> N;
int C;
cin >> C;
int V;
cin >> V;
repeat(i, V - 1 + 1) { cin >> S[i]; }
repeat(i, V - 1 + 1) { cin >> T[i]; }
repeat(i, V - 1 + 1) { cin >> Y[i]; }
repeat(i, V - 1 + 1) { cin >> M[i]; }
```
