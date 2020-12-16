from setuptools import setup
from setuptools import find_packages

version = "8.4.2.dev0"

long_description = "\n\n".join(
    [open("README.rst").read(), open("CHANGES.rst").read()])

setup(
    name="collective.solr",
    version=version,
    description="Solr integration for external indexing and searching.",
    long_description=long_description,
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Web Environment",
        "Framework :: Plone",
        "Framework :: Plone :: 4.3",
        "Framework :: Plone :: 5.0",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
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
        "Products.CMFPlone >= 4.3.7",
        "Products.GenericSetup",
        "Products.ZCatalog",
        # 'collective.indexing >= 2.1',
        "collective.js.showmore",
        "lxml",
        "plone.app.content",
        "plone.app.layout",
        "plone.app.registry",
        "plone.app.vocabularies",
        "plone.api",
        "plone.browserlayer",
        "plone.indexer",
        "plone.restapi",
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
        "test4": [
            "Products.LinguaPlone >=3.1a1",
            "plone.app.robotframework[debug]",
            "plone.app.testing[robot]",
        ],
    },
    entry_points="""
      [z3c.autoinclude.plugin]
      target=plone
      [zopectl.command]
      solr_activate=collective.solr.commands:solr_activate
      solr_deactivate=collective.solr.commands:solr_deactivate
      solr_clear_index=collective.solr.commands:solr_clear_index
      solr_reindex=collective.solr.commands:solr_reindex
    """,
)
