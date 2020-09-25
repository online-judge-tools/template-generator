# Contribution and Hacking Guide

links:

-   [CONTRIBUTING.md](https://github.com/online-judge-tools/.github/blob/master/CONTRIBUTING.md) of [online-judge-tools](https://github.com/online-judge-tools) organization
-   [DESIGN.md](https://github.com/online-judge-tools/template-generator/blob/master/DESIGN.md)


## How to add a new generator for a new language

Do following steps:

1.  Make a file `onlinejudge_template/generator/YOUR_LANGUAGE.py` in a way similar to other files
1.  Make a template file `onlinejudge_template_resources/template/YOUR_TEMPLATE.EXT` in a way similar to other files
1.  Add tests to `tests/` if possible


## Natural language processing

A person who can do natural language processing (mainly English, probably in the classical way) is required.
We want to analyze the problem statements and constraints section and retrieve more information (e.g. what variables mean graphs or trees, what variables are under modulo).
