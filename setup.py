#!/usr/bin/env python3

from setuptools import setup, find_packages

exec(open('people/version.py').read())

setup(
    name='people',
    version=__version__,
    description='An activity and location model of urban citizens.',
    maintainer='Tim Tröndle',
    maintainer_email='tt397@cam.ac.uk',
    url='https://www.github.com/timtroendle/people',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=['pykov==1.1'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering'
    ]
)
