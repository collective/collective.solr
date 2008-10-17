from zope.component import queryAdapter
from DateTime import DateTime
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import _checkPermission
from Products.CMFPlone.CatalogTool import CatalogTool

from collective.solr.interfaces import ISearchDispatcher
from collective.indexing.utils import autoFlushQueue


def searchResults(self, REQUEST=None, **kw):
    """ based on the version in `CMFPlone/CatalogTool.py` """
    kw = kw.copy()
    show_inactive = kw.get('show_inactive', False)
    user = _getAuthenticatedUser(self)
    kw['allowedRolesAndUsers'] = self._listAllowedRolesAndUsers(user)
    if not show_inactive and not _checkPermission(AccessInactivePortalContent, self):
        kw['effectiveRange'] = DateTime()

    # support collective.indexing's "auto-flush" feature
    # see http://dev.plone.org/collective/changeset/73602
    autoFlushQueue()

    adapter = queryAdapter(self, ISearchDispatcher)
    if adapter is not None:
        return adapter(REQUEST, **kw)
    else:
        return ZCatalog.searchResults(self, REQUEST, **kw)


def patchCatalogTool():
    """ monkey patch plone's catalogtool with the solr dispatcher """
    CatalogTool.searchResults = searchResults
    CatalogTool.__call__ = searchResults

