from logging import getLogger

from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
from ZODB.POSException import POSKeyError

logger = getLogger('collective.solr.indexer')

class ContentStreamView(BrowserView):

    def __call__(self, uid):
        uid_catalog = getToolByName(self.context, 'uid_catalog')
        brains = uid_catalog(UID=uid)
        if brains and len(brains) == 1:
            obj = brains[0].getObject()
            path_string = brains[0].getPath()
        else:
            return ''
        field = obj.getPrimaryField()   
        try:
            binary_data = str(field.get(obj).data)
        except POSKeyError:
            logger.warn('Error: No blob @ %s', path_string)
            return ''
        except AttributeError:
            logger.warn('Error: Wrong field contents @ %s', path_string)
            return ''
        if not binary_data:
            return ''
        return binary_data
