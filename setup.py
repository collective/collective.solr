import os.path
from setuptools import setup
from setuptools import find_packages

version = '4.1.1.dev0'
long_description = \
    open("README.rst").read() + '\n' + \
    open(os.path.join('docs', 'CHANGES.rst')).read() + \
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
        'Framework :: Plone :: 4.2',
        'Framework :: Plone :: 4.3',
        'Framework :: Plone :: 5.0',
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
    author='Jarn AS',
    author_email='info@jarn.com',
    maintainer='Plone Community',
    maintainer_email='plone-developers@lists.sourceforge.net',
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
        'Products.GenericSetup',
        'Unidecode',
        'ZODB3',
        'Zope2 >= 2.13',
        'archetypes.schemaextender',
        'collective.indexing >= 2.0a2',
        'collective.js.showmore',
        'plone.app.content',
        'plone.app.layout',
        'plone.app.testing',
        'plone.app.vocabularies',
        'plone.api',
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
            'plone.app.testing[robot]',
            'plone.app.robotframework',
        ],
        'test4': [
            'Products.LinguaPlone >=3.1a1',
            'plone.app.contentlisting',  # Comes with Plone 4.2,
                                         # only a test req for 4.1 compat
            'plone.app.testing[robot]',
        ]
    },
    entry_points='''
      [z3c.autoinclude.plugin]
      target=plone
      [zopectl.command]
      solr_clear_index=collective.solr.commands:solr_clear_index
    ''',
)
