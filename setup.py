#!/usr/bin/env python
# -*- coding:utf-8 -*-

from setuptools import setup, find_packages

from opps import promos


install_requires = ["opps", 'django-endless-pagination==1.1']

classifiers = ["Development Status :: 4 - Beta",
               "Intended Audience :: Developers",
               "License :: OSI Approved :: MIT License",
               "Operating System :: OS Independent",
               "Framework :: Django",
               'Programming Language :: Python',
               "Programming Language :: Python :: 2.7",
               "Operating System :: OS Independent",
               "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
               'Topic :: Software Development :: Libraries :: Python Modules']

try:
    long_description = open('README.md').read()
except:
    long_description = promos.__description__

setup(
    name='opps-promos',
    namespace_packages=['opps', 'opps.promos'],
    version=promos.__version__,
    description=promos.__description__,
    long_description=long_description,
    classifiers=classifiers,
    keywords='promos opps cms django apps magazines websites',
    author=promos.__author__,
    author_email=promos.__email__,
    url='http://oppsproject.org',
    download_url="https://github.com/opps/opps-promos/tarball/master",
    license=promos.__license__,
    packages=find_packages(exclude=('doc', 'docs',)),
    package_dir={'opps': 'opps'},
    install_requires=install_requires,
    include_package_data=True,
    package_data={
        'promos': ['templates/*']
    }
)
