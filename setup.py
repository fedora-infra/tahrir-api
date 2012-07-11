import os

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
    'SQLAlchemy',
    'zope.sqlalchemy',
    'mysql-python'
    ]

setup(name='tahrir-api',
      version='0.1.3.6',
      description='An API for interacting with the Tahrir database',
      long_description=README,
      license="AGPLv3+",
      classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
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

