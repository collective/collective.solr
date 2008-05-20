from zope.component import queryUtility

from collective.solr.interfaces import ISolrConnectionManager


def isActive():
    """ indicate if the solr connection should/can be used """
    manager = queryUtility(ISolrConnectionManager)
    if manager is not None:
        return manager.isActive()
    return False


def prepareData(data):
    """ modify data according to solr specifics, i.e. replace ':' by '$'
        for "allowedRolesAndUsers" etc """
    allowed = data.get('allowedRolesAndUsers', None)
    if allowed is not None:
        data['allowedRolesAndUsers'] = [r.replace(':','$') for r in allowed]

