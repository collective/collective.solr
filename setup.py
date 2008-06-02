from setuptools import setup, find_packages
import os

version = '0.1.jarn.3'

setup(name='collective.solr',
      version=version,
      description="Solr search integration",
      long_description=open("README.txt").read() + "\n" +
                       open(os.path.join("docs", "HISTORY.txt")).read(),
      # Get more strings from http://www.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='',
      author='Jarn AS',
      author_email='info@jarn.com',
      url='http://www.jarn.com',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'elementtree',
          'collective.indexing',
      ],
      entry_points="""
      # -*- Entry points: -*-
      """,
      )
