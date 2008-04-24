from zope.interface import implements
from collective.solr.interfaces import ISearch


class Search(object):
    """ a search utility for solr """
    implements(ISearch)

    def search(self, **query):
        """ perform a search with the given parameters """
        pass

