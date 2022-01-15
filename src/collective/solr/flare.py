import sys

from collective.solr.interfaces import IFlare, ISolrFlare
from collective.solr.parser import AttrDict
from DateTime import DateTime
from OFS.Traversable import path2url
from Products.CMFPlone.utils import pretty_title_or_id
from zope.component import adapts
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.publisher.interfaces.http import IHTTPRequest

timezone = DateTime().timezone()


@implementer(IFlare)
class PloneFlare(AttrDict):
    """a sol(a)r brain, i.e. a data container for search results"""

    adapts(ISolrFlare, IHTTPRequest)

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, context, request=None):
        self.context = context
        self.request = request
        self.update(context)  # copy data

    @property
    def id(self):
        """convenience alias"""
        return self.get("id", self.get("getId"))

    def getPath(self):
        """convenience alias"""
        return self["path_string"]

    def getRID(self):
        """Return a record id"""
        return int(int(self["UID"], 16) % sys.maxsize)

    def getObject(self, REQUEST=None, restricted=True):
        """return the actual object corresponding to this flare while
        mimicking what publisher's traversal does, i.e. potentially
        allowing access to the final object even if intermediate objects
        cannot be accessed (much like the original implementation in
        `ZCatalog.CatalogBrains.AbstractCatalogBrain`)"""
        site = getSite()
        path = self.getPath()
        if not path:
            return None
        path = path.split("/")
        if restricted:
            parent = site.unrestrictedTraverse(path[:-1])
            return parent.restrictedTraverse(path[-1])
        return site.unrestrictedTraverse(path)

    def _unrestrictedGetObject(self):
        return self.getObject(restricted=False)

    def getURL(self, relative=False):
        """convert the physical path into a url, if it was stored"""
        path = self.getPath()
        path = path
        try:
            url = self.request.physicalPathToURL(path, relative)
        except AttributeError:
            url = path2url(path.split("/"))
        return url

    def pretty_title_or_id(self):
        context = getSite()
        return pretty_title_or_id(context, self)

    @property
    def CreationDate(self):
        created = self.get("created", None)
        if created is None:
            return "n.a."
        return created.toZone(timezone).ISO8601()

    @property
    def ModificationDate(self):
        modified = self.get("modified", None)
        if modified is None:
            return "n.a."
        return modified.toZone(timezone).ISO8601()

    @property
    def data_record_normalized_score_(self):
        score = self.get("score", None)
        if score is None:
            return "n.a."
        return "%.1f" % (float(score) * 100)

    @property
    def review_state(self):
        if "review_state" in self:
            return self["review_state"]
        return ""
