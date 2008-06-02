from zope.component import queryUtility

from collective.solr.interfaces import ISolrConnectionConfig


def isActive():
    """ indicate if the solr connection should/can be used """
    config = queryUtility(ISolrConnectionConfig)
    if config is not None:
        return config.active
    return False


def activate(active=True):
    """ (de)activate the solr integration """
    config = queryUtility(ISolrConnectionConfig)
    config.active = active


def prepareData(data):
    """ modify data according to solr specifics, i.e. replace ':' by '$'
        for "allowedRolesAndUsers" etc """
    allowed = data.get('allowedRolesAndUsers', None)
    if allowed is not None:
        data['allowedRolesAndUsers'] = [r.replace(':','$') for r in allowed]

