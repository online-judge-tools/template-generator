import argparse
import os
import subprocess
import sys
from logging import DEBUG, INFO, basicConfig, getLogger

import onlinejudge_template.analyzer
import onlinejudge_template.generator

import onlinejudge

logger = getLogger(__name__)


def prepare_problem(problem: onlinejudge.type.Problem) -> None:
    table = {
        'main.cpp': 'template.cpp',
        'generate.py': 'generate.py',
    }

    soup = onlinejudge_template.analyzer.download_html(problem.get_url())
    for dest, template in table.items():
        node = onlinejudge_template.analyzer.run(soup, url=problem.get_url())
        code = onlinejudge_template.generator.run(node, template_file=template)
        with open(dest, 'wb') as fh:
            fh.write(code)
    subprocess.check_call(['oj', 'download', problem.get_url()], stdout=sys.stdout, stderr=sys.stderr)


def prepare_contest(contest: onlinejudge.type.Contest) -> None:
    for i, problem in enumerate(contest.list_problems()):
        if isinstance(problem, onlinejudge.service.atcoder.AtCoderProblem):
            alphabet = problem.problem_id
        elif isinstance(problem, onlinejudge.service.codeforces.CodeforcesProblem):
            alphabet = problem.problem_id
        else:
            alphabet = str(i)

        os.mkdir(alphabet)
        os.chdir(alphabet)
        try:
            prepare_problem(problem)
        finally:
            os.chdir('..')


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)

    problem = onlinejudge.dispatch.problem_from_url(args.url)
    contest = onlinejudge.dispatch.contest_from_url(args.url)
    if problem is not None:
        prepare_problem(problem)
    elif contest is not None:
        prepare_contest(contest)
    else:
        raise ValueError(f"""unrecognized URL: {args.url}""")


if __name__ == '__main__':
    main()
