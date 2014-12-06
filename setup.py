from __future__ import print_function
from setuptools import setup

import os
import sys


if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.md').read()

dependencies = []
with open('requirements.txt', 'r') as f:
    for line in f:
        dependencies.append(line)

setup(
    name='agave_common',
    version=open('common/VERSION').read().strip(),
    description='Python package for building services for the Agave platform.',
    long_description=readme,
    author='Joe Stubbs',
    author_email='jstubbs@tacc.utexas.edu',
    url='https://bitbucket.org/jstubbs/agave_common',
    packages=[
        'common'
    ],
    install_requires=dependencies,
    include_package_data=True,
    # data_files=[('etc', ['adama.conf'])],
    license="MIT",
    zip_safe=False,
    keywords='agave_common',
    classifiers=[
        'Development Status :: 1 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.7',
    ],
    test_suite='tests',
)
