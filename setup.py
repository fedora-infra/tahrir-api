import codecs
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
    ],
}

TESTS_REQUIRE = [
    'fudge',
    'pyhamcrest',
    'zope.testrunner',
]


def _read(fname):
    with codecs.open(fname, encoding='utf-8') as f:
        return f.read()


setup(
    name='tahrir-api',
    version=_read('version.txt').strip(),
    author='Ross Delinger',
    author_email='rdelinge@redhat.com',
    description="An API for interacting with the Tahrir database",
    long_description=(_read('README.rst') + '\n\n' + _read('CHANGES.rst')),
    license="GPLv3+",
    keywords='web sqlalchemy api',
    classifiers=[
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: "
        "GNU General Public License v3 or later (GPLv3+)",
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
    ],
    url="https://github.com/NextThought/nti.tahrir-api",
    zip_safe=True,
    packages=find_packages("src"),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=[
        'setuptools',
        'alembic',
        'arrow',
        'pastedeploy',
        'pygments',
        'simplejson',
        'six',
        'SQLAlchemy',
        'zope.sqlalchemy',
    ],
    test_suite="tahrir-api.tests",
    extras_require={
        'test': TESTS_REQUIRE,
        'docs': [
            'Sphinx',
            'repoze.sphinx.autointerface',
            'sphinx_rtd_theme',
        ],
    },
)
