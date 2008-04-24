from logging import getLogger
from zope.interface import implements
from collective.solr.interfaces import ISearch

logger = getLogger('collective.solr.search')


class Search(object):
    """ a search utility for solr """
    implements(ISearch)

    def search(self, **query):
        """ perform a search with the given parameters """
        pass

