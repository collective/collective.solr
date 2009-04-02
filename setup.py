from setuptools import setup, find_packages
from os.path import join

version = open(join('src', 'collective', 'solr', 'version.txt')).read().strip()
readme = open("README.txt").read()
history = open(join('docs', 'HISTORY.txt')).read()

setup(name = 'collective.solr',
      version = version,
      description = 'Solr integration for external indexing and searching.',
      long_description = readme[readme.find('\n\n'):] + '\n' + history,
      classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Plone',
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        'Intended Audience :: Other Audience',
        'License :: OSI Approved :: GNU General Public License (GPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
      ],
      keywords = 'plone cmf zope indexing searching solr lucene',
      author = 'Plone Foundation',
      author_email = 'plone-developers@lists.sourceforge.net',
      url = 'http://plone.org/products/collective.solr',
      download_url = 'http://cheeseshop.python.org/pypi/collective.solr/',
      license = 'GPL',
      packages = find_packages('src'),
      package_dir = {'': 'src'},
      namespace_packages = ['collective'],
      include_package_data = True,
      platforms = 'Any',
      zip_safe = False,
      install_requires=[
          'setuptools',
          'elementtree',
          'collective.indexing',
          'plone.browserlayer',
      ],
      entry_points = '',
)
