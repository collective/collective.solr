from zope.component import queryUtility
from Acquisition import aq_base

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


def findObjects(origin):
    """ generator to recursively find and yield all zope objects below
        the given start point """
    traverse = origin.unrestrictedTraverse
    base = '/'.join(origin.getPhysicalPath())
    cut = len(base) + 1
    paths = [ base ]
    for idx, path in enumerate(paths):
        obj = traverse(path)
        yield path[cut:], obj
        if hasattr(aq_base(obj), 'objectIds'):
            for id in obj.objectIds():
                paths.insert(idx + 1, path + '/' + id)

