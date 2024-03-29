from collective.solr.interfaces import ISearchDispatcher
from DateTime import DateTime
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFPlone.CatalogTool import CatalogTool
from zope.component import queryAdapter


def searchResults(self, REQUEST=None, **kw):
    """based on the version in `CMFPlone/CatalogTool.py`"""
    kw = kw.copy()
    only_active = not kw.get("show_inactive", False)
    user = _getAuthenticatedUser(self)
    kw["allowedRolesAndUsers"] = self._listAllowedRolesAndUsers(user)
    if only_active and not self.allow_inactive(kw):
        kw["effectiveRange"] = DateTime()

    adapter = queryAdapter(self, ISearchDispatcher)
    if adapter is not None:
        return adapter(REQUEST, **kw)
    else:
        return self._cs_old_searchResults(REQUEST, **kw)


def patchCatalogTool():
    """monkey patch plone's catalogtool with the solr dispatcher"""
    if not hasattr(CatalogTool, "_cs_old_searchResults"):
        CatalogTool._cs_old_searchResults = CatalogTool.searchResults
        CatalogTool.searchResults = searchResults
        CatalogTool.__call__ = searchResults
