<%! import onlinejudge_template.generator.python as python %>\
#!/usr/bin/env python3
import random

# usage: $ oj generate-input 'python3 generate.py'
def main():
${python.generate_input(data)}
${python.write_input(data)}

if __name__ == "__main__":
    main()
