import os.path
from setuptools import setup
from setuptools import find_packages

version = '4.1.1.dev0'
long_description = \
    open('README.rst').read() + '\n' + \
    open('CHANGES.rst').read() + \
    open(os.path.join('docs', 'credits.rst')).read() + \
    open(os.path.join('docs', 'contributors.rst')).read(),

setup(
    name='collective.solr',
    version=version,
    description='Solr integration for external indexing and searching.',
    long_description=long_description,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='plone cmf zope indexing searching solr lucene',
    author='Plone Community',
    author_email='plone-developers@lists.sourceforge.net',
    maintainer='Timo Stollenwerk',
    maintainer_email='tisto@plone.org',
    url='https://github.com/collective/collective.solr',
    license='GPL version 2',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    namespace_packages=['collective'],
    include_package_data=True,
    platforms='Any',
    zip_safe=False,
    install_requires=[
        'Acquisition',
        'DateTime',
        'Plone >= 4.1',
        'Products.Archetypes',
        'Products.CMFCore',
        'Products.CMFDefault',
        'Products.GenericSetup',
        'Unidecode',
        'ZODB3',
        'Zope2 >= 2.13',
        'archetypes.schemaextender',
        'argparse',  # we need to support Python 2.6 (Plone 4.x)
        'collective.indexing >= 2.0a2',
        'collective.js.showmore',
        'plone.app.content',
        'plone.app.controlpanel',
        'plone.app.layout',
        'plone.app.vocabularies',
        'plone.browserlayer',
        'plone.indexer',
        'setuptools',
        'transaction',
        'zope.component',
        'zope.formlib',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.publisher',
        'zope.schema',
    ],
    extras_require={
        'test': [
            'Products.LinguaPlone >=3.1a1',
            'plone.app.contentlisting',  # Comes with Plone 4.2,
                                         # only a test req for 4.1 compat
            'plone.app.testing',
        ]
    },
    entry_points='''
      [z3c.autoinclude.plugin]
      target=plone
      [zopectl.command]
      solr_clear_index=collective.solr.commands:solr_clear_index
      solr_reindex=collective.solr.commands:solr_reindex
    ''',
)
