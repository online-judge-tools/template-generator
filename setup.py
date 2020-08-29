#!/usr/bin/env python3
from setuptools import find_packages, setup

from onlinejudge_template.__about__ import __title__, __url__, __version__

setup(
    name=__title__,
    version=__version__,
    author='Kimiyuki Onaka',
    author_email='kimiyuki95@gmail.com',
    url=__url__,
    license='MIT License',
    description='A simple template generator for competitive programming',
    python_requires='>=3.6',
    install_requires=[
        'appdirs >= 1.4',
        'beautifulsoup4 >= 4.8',
        'colorlog >= 4.2.1',
        'Mako >= 1.1',
        'online-judge-api-client >= 10.3.0',
        'online-judge-tools >= 10',
        'ply >= 3',
        'pyyaml >= 5',
        'requests >= 2.23',
        'toml >= 0.10',
    ],
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={
        'onlinejudge_template_resources': ['*', 'template/*'],
    },
    entry_points={
        'console_scripts': [
            'oj-template = onlinejudge_template.main:main',
            'oj-prepare = onlinejudge_prepare.main:main',
        ],
    },
)
