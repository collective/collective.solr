from time import time
from zope.component import queryAdapter, queryUtility
from DateTime import DateTime
from Products.ZCatalog.Lazy import LazyCat
from Products.CMFCore.permissions import AccessInactivePortalContent
from Products.CMFCore.utils import _getAuthenticatedUser
from Products.CMFCore.utils import _checkPermission
from Products.CMFPlone.CatalogTool import CatalogTool

from collective.solr.interfaces import ISearchDispatcher
from collective.indexing.utils import autoFlushQueue
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.parser import SolrResponse


def searchResults(self, REQUEST=None, **kw):
    """ based on the version in `CMFPlone/CatalogTool.py` """
    kw = kw.copy()
    only_active = not kw.get('show_inactive', False)
    user = _getAuthenticatedUser(self)
    kw['allowedRolesAndUsers'] = self._listAllowedRolesAndUsers(user)
    if only_active and not _checkPermission(AccessInactivePortalContent, self):
        config = queryUtility(ISolrConnectionConfig)
        steps = config.effective_steps
        kw['effectiveRange'] = DateTime(time()//steps*steps)

    # support collective.indexing's "auto-flush" feature
    # see http://dev.plone.org/collective/changeset/73602
    autoFlushQueue(hint='restricted/solr search', request=REQUEST, **kw)

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


def lazyAdd(self, other):
    if isinstance(other, SolrResponse):
        other = LazyCat([list(other)])
    return LazyCat._solr_original__add__(self, other)


def patchLazyCat():
    """ monkey patch ZCatalog's Lazy class in order to be able to
        concatenate `LazyCat` and `SolrResponse` instances """
    LazyCat._solr_original__add__ = LazyCat.__add__
    LazyCat.__add__ = lazyAdd
