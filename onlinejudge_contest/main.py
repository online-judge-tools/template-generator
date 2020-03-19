import argparse
import contextlib
import os
import pathlib
import subprocess
import sys
import urllib.parse
from logging import DEBUG, INFO, basicConfig, getLogger
from typing import *

import appdirs
import onlinejudge_template.analyzer.combined
import onlinejudge_template.generator
import onlinejudge_template.network
import toml

import onlinejudge

logger = getLogger(__name__)


@contextlib.contextmanager
def chdir(dir: pathlib.Path) -> Iterator[None]:
    cwd = pathlib.Path.cwd()
    dir.mkdir(parents=True, exist_ok=True)
    os.chdir(dir)
    try:
        yield
    finally:
        os.chdir(cwd)


def get_directory(*, problem: onlinejudge.type.Problem, contest: Optional[onlinejudge.type.Contest], config: Dict[str, Any]) -> pathlib.Path:
    service = problem.get_service()

    if contest is None:
        try:
            contest = problem.get_contest()
        except:
            pass
    for name in ('contest_id', 'contest_slug'):
        contest_id = getattr(contest, name, None)
        if contest_id:
            break
    else:
        contest_id = ''

    for name in ('problem_id', 'problem_slug', 'problem_no', 'task_id', 'task_slug', 'task_no', 'alphabet', 'index'):
        problem_id = getattr(problem, name, None)
        if problem_id:
            break
    else:
        problem_id, = urllib.parse.urlparse(problem.get_url()).path.lstrip('/').replace('/', '-'),

    params = {
        'service_name': service.get_name(),
        'service_domain': urllib.parse.urlparse(service.get_url()).netloc,
        'contest_id': contest_id,
        'problem_id': problem_id,
    }
    pattern = config.get('problem_directory')
    if pattern is None:
        pattern = str(pathlib.Path.home() / '{service_domain}' / '{contest_id}' / '{problem_id}')
        logger.info('setting "problem_directory" is not found in your config; use %s', repr(pattern))
    return pathlib.Path(pattern.format(**params)).expanduser()


def prepare_problem(problem: onlinejudge.type.Problem, *, contest: Optional[onlinejudge.type.Contest] = None, config: Dict[str, Any]) -> None:
    table = config.get('templates')
    if table is None:
        table = {
            'main.cpp': 'template.cpp',
            'generate.py': 'generate.py',
        }
        logger.info('setting "templates" is not found in your config; use %s', repr(table))

    dir = get_directory(problem=problem, contest=contest, config=config)
    logger.info('use directory: %s', str(dir))

    with chdir(dir):
        url = problem.get_url()
        html = onlinejudge_template.network.download_html(url)
        sample_cases = onlinejudge_template.network.download_sample_cases(url)

        # analyze
        resources = onlinejudge_template.analyzer.combined.prepare_from_html(html, url=url, sample_cases=sample_cases)
        analyzed = onlinejudge_template.analyzer.combined.run(resources)

        for dest_str, template in table.items():
            dest = dir / dest_str

            # generate
            try:
                code = onlinejudge_template.generator.run(analyzed, template_file=template)
            except NotImplementedError as e:
                logger.error('generator failed: %s', e)
                continue

            # write
            dest.parent.mkdir(parents=True, exist_ok=True)
            if dest.exists():
                logger.error('file already exists: %s', str(dest))
            else:
                logger.info('write file: %s', str(dest))
                with open(dest, 'wb') as fh:
                    fh.write(code)

        # download
        try:
            subprocess.check_call(['oj', 'download', problem.get_url()], stdout=sys.stdout, stderr=sys.stderr)
        except subprocess.CalledProcessError as e:
            logger.error('samples downloader failed: %s', e)


def prepare_contest(contest: onlinejudge.type.Contest, *, config: Dict[str, Any]) -> None:
    for i, problem in enumerate(contest.list_problems()):
        prepare_problem(problem, contest=contest, config=config)


def get_config() -> Dict[str, Any]:
    config_path = pathlib.Path(appdirs.user_config_dir('online-judge-tools')) / 'oj2.config.toml'
    logger.info('config path: %s', str(config_path))
    if config_path.exists():
        return dict(**toml.load(config_path))
    else:
        return {}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('url')
    parser.add_argument('-v', '--verbose', action='store_true')
    args = parser.parse_args()

    if args.verbose:
        basicConfig(level=DEBUG)
    else:
        basicConfig(level=INFO)

    config = get_config()
    logger.info('config: %s', config)

    problem = onlinejudge.dispatch.problem_from_url(args.url)
    contest = onlinejudge.dispatch.contest_from_url(args.url)
    if problem is not None:
        prepare_problem(problem, config=config)
    elif contest is not None:
        prepare_contest(contest, config=config)
    else:
        raise ValueError(f"""unrecognized URL: {args.url}""")


if __name__ == '__main__':
    main()
