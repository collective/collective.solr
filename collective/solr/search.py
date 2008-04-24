from logging import getLogger
from zope.interface import implements
from collective.solr.interfaces import ISearch
from re import compile

logger = getLogger('collective.solr.search')


word = compile('^\w+$')
special = compile('([-+&|!(){}[\]^"~*?\\:])')

def quote(term):
    """ quote a given term according to the solr/lucene query syntax;
        see http://lucene.apache.org/java/docs/queryparsersyntax.html """
    if not word.match(term):
        term = '"%s"' % special.sub(r'\\\1', term)
    return term


class Search(object):
    """ a search utility for solr """
    implements(ISearch)

    def search(self, **query):
        """ perform a search with the given parameters """
        pass

