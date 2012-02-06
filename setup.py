from setuptools import setup, find_packages

version = '3.0'


setup(name = 'collective.solr',
      version = version,
      description = 'Solr integration for external indexing and searching.',
      long_description = open("README.rst").read() + '\n' +
                         open('CHANGES.txt').read(),
      classifiers = [
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
      keywords = 'plone cmf zope indexing searching solr lucene',
      author = 'Jarn AS',
      author_email = 'info@jarn.com',
      url = 'http://plone.org/products/collective.solr',
      license = 'GPL version 2',
      packages = find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages = ['collective'],
      include_package_data = True,
      platforms = 'Any',
      zip_safe = False,
      install_requires=[
        'Acquisition',
        'archetypes.schemaextender',
        'collective.indexing >= 2.0a2',
        'collective.js.showmore',
        'DateTime',
        'elementtree',
        'Plone >= 4.1',
        'plone.app.content',
        'plone.app.controlpanel',
        'plone.app.layout',
        'plone.app.vocabularies',
        'plone.browserlayer',
        'plone.indexer',
        'Products.Archetypes',
        'Products.CMFCore',
        'Products.CMFDefault',
        'Products.GenericSetup',
        'setuptools',
        'transaction',
        'Unidecode',
        'ZODB3',
        'zope.component',
        'zope.formlib',
        'zope.i18nmessageid',
        'zope.interface',
        'zope.publisher',
        'zope.schema',
        'Zope2 >= 2.13',
      ],
      extras_require = {'test': [
        'cElementTree',
        'collective.testcaselayer',
        'Products.LinguaPlone >=3.1a1',
        'Products.PloneTestCase',
      ]},
      entry_points = '''
        [z3c.autoinclude.plugin]
        target = plone
        [zopectl.command]
        solr_clear_index = collective.solr.commands:solr_clear_index
      ''',
)
