import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
README = open(os.path.join(here, 'README.rst')).read()

requires = [
    'SQLAlchemy',
    'zope.sqlalchemy',
    ]

setup(name='tahrir-api',
      version='0.1.2',
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
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      entry_points="""
      [console_scripts]
      initialize_tahrir_db = tahrir_api.scripts.initializedb:main
      """
      )

