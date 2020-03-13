#!/usr/bin/env python3
from setuptools import find_packages, setup

setup(
    name='online-judge-template-generator',
    version='2.0.0',
    author='Kimiyuki Onaka',
    author_email='kimiyuki95@gmail.com',
    url='https://github.com/kmyk/online-judge-template-generator',
    license='MIT License',
    description='',
    python_requires='>=3.6',
    install_requires=[
        'beautifulsoup4 >= 4.8',
        'Mako >= 1.1',
        'online-judge-tools >= 9',
        'ply >= 3',
        'pyyaml >= 5',
        'requests >= 2.23',
        'sympy >= 1.5',
    ],
    packages=find_packages(exclude=('tests', 'docs')),
    package_data={
        'onlinejudge_template_resources': ['*'],
    },
    entry_points={
        'console_scripts': [
            'oj-template = onlinejudge_template.main:main',
        ],
    },
)
