from copy import deepcopy
from logging import getLogger

from Acquisition import aq_base
from collective.solr.exceptions import FallBackException
from collective.solr.interfaces import IFlare, ISearch, ISearchDispatcher
from collective.solr.monkey import patchCatalogTool
from collective.solr.parser import SolrResponse
from collective.solr.utils import isActive, padResults
from Missing import MV
from plone.registry.interfaces import IRegistry
from Products.ZCatalog.ZCatalog import ZCatalog
from zope.component import getUtility, queryMultiAdapter, queryUtility
from zope.component.hooks import getSite
from zope.interface import implementer
from zope.publisher.interfaces.http import IHTTPRequest

patchCatalogTool()  # patch catalog tool to use the dispatcher...


logger = getLogger("collective.solr.dispatcher")


@implementer(ISearchDispatcher)
class SearchDispatcher(object):
    """adapter for potentially dispatching a given query to an
    alternative search backend (instead of the portal catalog)"""

    def __init__(self, context):
        self.context = context

    def __call__(self, request, **keywords):
        """decide on a search backend and perform the given query"""
        if isActive():
            try:
                return solrSearchResults(request, **keywords)
            except FallBackException:
                pass
        if getattr(aq_base(self.context), "_cs_old_searchResults", None):
            return self.context._cs_old_searchResults(request, **keywords)
        return ZCatalog.searchResults(self.context, request, **keywords)


def solrSearchResults(request=None, **keywords):
    """perform a query using solr after translating the passed in
    parameters with portal catalog semantics"""
    site = getSite()
    search = queryUtility(ISearch, context=site)
    if search is None:
        logger.warning("No search utility found in site %s", site)
        raise FallBackException

    registry = getUtility(IRegistry)
    config_required = registry["collective.solr.required"]

    if request is None:
        # try to get a request instance, so that flares can be adapted to
        # ploneflares and urls can be converted into absolute ones etc;
        # however, in this case any arguments from the request are ignored
        args = deepcopy(keywords)
        request = getattr(site, "REQUEST", None)
    elif IHTTPRequest.providedBy(request):
        args = deepcopy(request.form)
        args.update(keywords)  # keywords take precedence
    else:
        assert isinstance(request, dict), request
        args = deepcopy(request)
        args.update(keywords)  # keywords take precedence
        # if request is a dict, we need the real request in order to
        # be able to adapt to plone flares
        request = getattr(site, "REQUEST", args)

    if "path" in args and "navtree" in args["path"]:
        raise FallBackException  # we can't handle navtree queries yet

    use_solr = args.get("use_solr", False)  # A special key to force Solr
    if not use_solr and config_required:
        required = set(config_required).intersection(args)
        if required:
            for key in required:
                if not args[key]:
                    raise FallBackException
        else:
            raise FallBackException

    core = args.get("core", None)
    query, params = search.buildQueryAndParameters(**args)

    if query != {}:
        __traceback_info__ = (query, params, args)
        if core is not None:
            params["core"] = core
        response = search(query, **params)
    else:
        return SolrResponse()

    def wrap(flare):
        """wrap a flare object with a helper class"""
        adapter = queryMultiAdapter((flare, request), IFlare)
        return adapter is not None and adapter or flare

    schema = search.getManager(core=core).getSchema() or {}
    results = response.results()
    for idx, flare in enumerate(results):
        flare = wrap(flare)
        for missing in set(schema.stored).difference(flare):
            flare[missing] = MV
        results[idx] = wrap(flare)
    padResults(results, **params)  # pad the batch
    return response
