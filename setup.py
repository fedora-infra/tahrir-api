__requires__ = 'SQLAlchemy>=0.7.0'

import os
import sys

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

#silly-ness to make tests work
try:
    import multiprocessing
    import logging
except ImportError:
    pass

requires = [
    'pastedeploy',
    'pygments',
    'simplejson',
    'SQLAlchemy>=0.7.0',
    'zope.sqlalchemy',
    'alembic'
]

if sys.version_info[0] == 2 and sys.version_info[1] <= 6:
    requires.extend([
        'ordereddict',
    ])


setup(name='tahrir-api',
      version='0.4.2',
      description='An API for interacting with the Tahrir database',
      long_description=README,
      license="GPLv3+",
      classifiers=["Programming Language :: Python",
                   "Framework :: Pyramid",
                   "Topic :: Internet :: WWW/HTTP",
                   "License :: OSI Approved :: "
                   "GNU General Public License v3 or later (GPLv3+)",
                   ],
      author='Ross Delinger',
      author_email='rdelinge@redhat.com',
      url='http://github.com/rossdylan/tahrir-api',
      keywords='web sqlalchemy api',
      packages=['tahrir_api', 'tahrir_api.scripts'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=[
          'nose',
      ],
      test_suite='nose.collector',
      entry_points="""
      [console_scripts]
      initialize_tahrir_db = tahrir_api.scripts.initializedb:main
      """
      )
