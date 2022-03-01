#!/usr/bin/env python

"""The setup script."""

from setuptools import setup, find_packages

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements/prod.txt') as prod_requirements_file:
    prod_requirements = prod_requirements_file.read().splitlines()
    if prod_requirements and prod_requirements[0].startswith('-r'):
        prod_requirements = prod_requirements[1:]

setup_requirements = []

test_requirements = []

setup(
    author="Fvieille",
    author_email='francois.vieille@mel.lincoln.fr',
    python_requires='>=3.5',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
    ],
    description="Projet Reponse Client de Fvieille",
    entry_points={
        'console_scripts': [
            'clients=clients.cli:main',
        ],
    },
    install_requires=prod_requirements,
    long_description=readme,
    long_description_content_type="text/markdown",
    include_package_data=True,
    keywords='clients',
    name='clients',
    packages=find_packages(include=['clients', 'clients.*']),
    setup_requires=setup_requirements,
    test_suite='tests',
    tests_require=test_requirements,
    url='https://github.com/prise6/reponse-client-s',
    version='0.1.0',
    zip_safe=False,
)
