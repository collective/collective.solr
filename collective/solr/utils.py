from zope.component import queryUtility

from collective.solr.interfaces import ISolrConnectionManager


def isActive():
    """ indicate if the solr connection should/can be used """
    manager = queryUtility(ISolrConnectionManager)
    if manager is not None:
        return manager.isActive()
    return False

