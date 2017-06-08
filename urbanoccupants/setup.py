#!/usr/bin/env python3

from setuptools import setup, find_packages

exec(open('urbanoccupants/version.py').read())

setup(
    name='urbanoccupants',
    version=__version__,
    description='A library accompanying the case study on urban occupancy in Haringey.',
    maintainer='Tim Tröndle',
    maintainer_email='tt397@cam.ac.uk',
    url='https://www.github.com/timtroendle/urbanoccupants',
    packages=find_packages(exclude=['tests*']),
    include_package_data=True,
    install_requires=['pytus2000'],
    classifiers=[
        'Environment :: Console',
        'Intended Audience :: Science/Research',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3 :: Only',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering'
    ]
)
