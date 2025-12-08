import sys

from setuptools import find_packages, setup

version = "10.1.0"

assert sys.version_info >= (
    3,
    9,
    0,
), "collective.solr 10 requires Python 3.10.0+. Please downgrade to collective.solr 9 for Plone 5.2, or collective.solr 8 for Python 2 and Plone 4.3/5.1."


long_description = "\n\n".join([open("README.rst").read(), open("CHANGES.rst").read()])

setup(
    name="collective.solr",
    version=version,
    description="Solr integration for external indexing and searching.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 6.0",
        "Framework :: Plone :: 6.1",
        "Framework :: Plone :: Addon",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
    ],
    keywords="plone cmf zope indexing searching solr lucene",
    author="Plone Community",
    author_email="plone-developers@lists.sourceforge.net",
    maintainer="Timo Stollenwerk",
    maintainer_email="tisto@plone.org",
    url="https://github.com/collective/collective.solr",
    license="GPL version 2",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["collective"],
    include_package_data=True,
    platforms="Any",
    zip_safe=False,
    install_requires=[
        "Acquisition",
        "DateTime",
        "Products.CMFCore",
        "Products.CMFPlone >= 6.0.0",
        "Products.GenericSetup",
        "Products.ZCatalog",
        "lxml",
        "plone.app.content",
        "plone.app.layout",
        "plone.app.registry",
        "plone.app.vocabularies",
        "plone.api",
        "plone.browserlayer",
        "plone.indexer",
        "plone.restapi",
        "requests-toolbelt",
        "setuptools",
        "transaction",
        "zope.component",
        "zope.i18nmessageid",
        "zope.interface",
        "zope.publisher",
        "zope.schema",
    ],
    extras_require={
        "test": ["plone.app.testing[robot]", "plone.app.robotframework[debug]"],
    },
    entry_points="""
      [z3c.autoinclude.plugin]
      target=plone
      [zopectl.command]
      solr_activate=collective.solr.commands:solr_activate
      solr_deactivate=collective.solr.commands:solr_deactivate
      solr_clear_index=collective.solr.commands:solr_clear_index
      solr_clear=collective.solr.commands:solr_clear_index
      solr_reindex=collective.solr.commands:solr_reindex
      solr_cleanup=collective.solr.commands:solr_cleanup
      solr_sync=collective.solr.commands:solr_sync
    """,
)
