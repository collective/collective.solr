# -*- coding: utf-8 -*-
from zope.component import queryAdapter
from DateTime import DateTime
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import _checkPermission
from Products.CMFPlone.CatalogTool import CatalogTool
from Products.ZCatalog.Lazy import Lazy
from Products.ZCatalog.Lazy import LazyCat

from collective.solr.interfaces import (ISearchDispatcher)
from collective.solr.parser import SolrResponse

HAS_EXPCAT = True
try:
    from experimental.catalogqueryplan import lazy
except ImportError:
    HAS_EXPCAT = False


def searchResults(self, REQUEST=None, **kw):
    """ based on the version in `CMFPlone/CatalogTool.py` """
    kw = kw.copy()
    only_active = not kw.get('show_inactive', False)
    user = _getAuthenticatedUser(self)
    kw['allowedRolesAndUsers'] = self._listAllowedRolesAndUsers(user)
    if only_active and not _checkPermission(AccessInactivePortalContent, self):
        kw['effectiveRange'] = DateTime()

    adapter = queryAdapter(self, ISearchDispatcher)
    if adapter is not None:
        return adapter(REQUEST, **kw)
    else:
        return self._cs_old_searchResults(REQUEST, **kw)


def patchCatalogTool():
    """ monkey patch plone's catalogtool with the solr dispatcher """
    CatalogTool._cs_old_searchResults = CatalogTool.searchResults
    CatalogTool.searchResults = searchResults
    CatalogTool.__call__ = searchResults

if HAS_EXPCAT:
    def lazyExpCatAdd(self, other):
        if isinstance(other, SolrResponse):
            other = lazy.LazyCat([list(other)])
        return lazy.Lazy._solr_original__add__(self, other)


def lazyAdd(self, other):
    if isinstance(other, SolrResponse):
        other = LazyCat([list(other)])
    return Lazy._solr_original__add__(self, other)


def patchLazy():
    """ monkey patch ZCatalog's Lazy class in order to be able to
        concatenate `Lazy` and `SolrResponse` instances """
    Lazy._solr_original__add__ = Lazy.__add__
    Lazy.__add__ = lazyAdd
    if HAS_EXPCAT:
        lazy.Lazy._solr_original__add__ = lazy.Lazy.__add__
        lazy.Lazy.__add__ = lazyExpCatAdd
