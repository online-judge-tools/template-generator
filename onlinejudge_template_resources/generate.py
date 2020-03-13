<%! import onlinejudge_template.generator.python as python %>\
#!/usr/bin/env python3
import random
import onlinejudge_random as random_oj

def main():
${python.generate_input(data=data)}
${python.write_input(data=data)}

if __name__ == "__main__":
    main()
