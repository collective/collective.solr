from zope.interface import implements
from zope.component import adapts
from zope.publisher.interfaces.http import IHTTPRequest
from OFS.Traversable import path2url
from DateTime import DateTime

from collective.solr.interfaces import ISolrFlare
from collective.solr.interfaces import IFlare
from collective.solr.parser import AttrDict

timezone = DateTime().timezone()


class PloneFlare(AttrDict):
    """ a sol(a)r brain, i.e. a data container for search results """
    implements(IFlare)
    adapts(ISolrFlare, IHTTPRequest)

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, context, request=None):
        self.context = context
        self.request = request
        self.update(context.__dict__)  # copy data

    def getURL(self):
        """ convert the physical path into a url, if it was stored;
            the code is copied from `OFS/Traversable.py` """
        url = 'unknown'
        path = self.get('getPhysicalPath', None)
        if path is not None:
            spp = path.split()
            try:
                url = self.request.physicalPathToURL(spp)
            except AttributeError:
                url = path2url(spp[1:])
        return url

    @property
    def pretty_title_or_id(self):
        for attr in 'Title', 'getId', 'id':
            if self.has_key(attr):
                return self[attr]
        return '<untitled item>'

    @property
    def ModificationDate(self):
        modified = self.get('modified', None)
        if modified is None:
            return 'n.a.'
        return modified.toZone(timezone).ISO()

    @property
    def data_record_normalized_score_(self):
        score = self.get('score', None)
        if score is None:
            return 'n.a.'
        return score

