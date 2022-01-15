from logging import getLogger
from time import time

import six
from collective.solr.exceptions import SolrInactiveException
from collective.solr.interfaces import ISearch, ISolrConnectionManager
from collective.solr.mangler import (
    cleanupQueryParameters,
    mangleQuery,
    optimizeQueryParameters,
    subtractQueryParameters,
)
from collective.solr.parser import SolrResponse
from collective.solr.queryparser import quote, quote_iterable_item
from collective.solr.utils import getConfig, isWildCard, prepare_wildcard, prepareData
from Missing import MV
from Products.CMFPlone.utils import safe_unicode
from six.moves import map
from zope.component import queryUtility
from zope.interface import implementer

try:
    from Products.LinguaPlone.catalog import languageFilter
except ImportError:

    def languageFilter(args):
        pass


logger = getLogger("collective.solr.search")


@implementer(ISearch)
class Search(object):
    """a search utility for solr"""

    def __init__(self):
        self.manager = None
        self.config = None

    def getManager(self):
        if self.manager is None:
            self.manager = queryUtility(ISolrConnectionManager)
        return self.manager

    def getConfig(self):
        if self.config is None:
            self.config = getConfig()
        return self.config

    def search(
        self,
        query,
        wt="xml",
        sow="true",
        lowercase_operator="true",
        default_operator="AND",
        **parameters
    ):
        """perform a search with the given querystring and parameters"""
        start = time()
        config = self.getConfig()
        manager = self.getManager()
        manager.setSearchTimeout()
        connection = manager.getConnection()
        if connection is None:
            raise SolrInactiveException
        parameters["wt"] = wt
        parameters["sow"] = sow  # split on whitespace
        parameters["lowercaseOperators"] = lowercase_operator
        parameters["q.op"] = default_operator
        if "rows" not in parameters:
            parameters["rows"] = config.max_results or 10000000
            # Check if rows param is 0 for backwards compatibility. Before
            # Solr 4 'rows = 0' meant that there is no limitation. Solr 4
            # always expects a rows param > 0 though:
            # http://wiki.apache.org/solr/CommonQueryParameters#rows
            if parameters["rows"] == 0:
                parameters["rows"] = 10000000
            logger.debug(
                'falling back to "max_results" (%d) without a "rows" '
                "parameter: %r (%r)",
                config.max_results,
                query,
                parameters,
            )
        if getattr(config, "highlight_fields", None):
            if parameters.get("hl", "false") == "true" and "hl.fl" not in parameters:
                parameters["hl"] = "true"
                parameters["hl.fl"] = config.highlight_fields or []
                parameters["hl.simple.pre"] = config.highlight_formatter_pre or " "
                parameters["hl.simple.post"] = config.highlight_formatter_post or " "
                parameters["hl.fragsize"] = (
                    getattr(config, "highlight_fragsize", None) or 100
                )
        if "fl" not in parameters:
            if config.field_list:
                parameters["fl"] = " ".join(config.field_list)
            else:
                parameters["fl"] = "* score"
        if isinstance(query, dict):
            query = u" ".join([safe_unicode(val) for val in query.values()])
        logger.debug("searching for %r (%r)", query, parameters)
        if "sort" in parameters:  # issue warning for unknown sort indices
            index, order = parameters["sort"].split()
            schema = manager.getSchema() or {}
            field = schema.get(index, None)
            if field is None or not field.stored:
                logger.warning('sorting on non-stored attribute "%s"', index)
        response = connection.search(q=query, **parameters)
        results = SolrResponse(response)
        response.close()
        manager.setTimeout(None)
        elapsed = (time() - start) * 1000
        slow = config.slow_query_threshold
        if slow and elapsed >= slow:
            logger.info(
                "slow query: %d/%d ms for %r (%r)",
                results.responseHeader["QTime"],
                elapsed,
                query,
                parameters,
            )
        logger.debug("highlighting info: %s" % getattr(results, "highlighting", {}))
        return results

    __call__ = search

    def buildQueryAndParameters(self, default=None, **args):
        """helper to build a querystring for simple use-cases"""
        schema = self.getManager().getSchema() or {}

        params = subtractQueryParameters(args)
        params = cleanupQueryParameters(params, schema)
        config = self.getConfig()

        languageFilter(args)
        prepareData(args)
        mangleQuery(args, config, schema)

        logger.debug('building query for "%r", %r', default, args)
        schema = self.getManager().getSchema() or {}
        # no default search field in Solr 7
        defaultSearchField = getattr(schema, "defaultSearchField", "SearchableText")
        args[None] = default
        query = {}

        for name, value in args.items():
            field_name = name
            if name and name[0] in "+-":
                field_name = name[1:]
            field = schema.get(field_name or defaultSearchField, None)
            if field is None or not field.indexed:
                logger.info(
                    'dropping unknown search attribute "%s" ' " (%r) for query: %r",
                    name,
                    value,
                    args,
                )
                continue
            if isinstance(value, bool):
                value = str(value).lower()
            elif not value:  # solr doesn't like empty fields (+foo:"")
                if not name:
                    continue
                logger.info(
                    'empty search term form "%s:%s", aborting buildQuery'
                    % (name, value)
                )
                return {}, params
            elif field.class_ == "solr.BoolField":
                if not isinstance(value, (tuple, list)):
                    value = [value]
                falses = "0", "False", MV
                true = lambda v: bool(v) and v not in falses
                value = set(map(true, value))
                if not len(value) == 1:
                    assert len(value) == 2  # just to make sure
                    continue  # skip when "true or false"
                value = str(value.pop()).lower()
            elif isinstance(value, (tuple, list)):
                # list items should be treated as literals, but
                # nevertheless only get quoted when necessary
                value = "(%s)" % " OR ".join(map(quote_iterable_item, value))
            elif isinstance(value, set):  # sets are taken literally
                if len(value) == 1:
                    query[name] = "".join(value)
                else:
                    query[name] = "(%s)" % " OR ".join(value)
                continue
            elif isinstance(value, six.string_types):
                if field.class_ == "solr.TextField":
                    if isWildCard(value):
                        value = prepare_wildcard(value)
                    value = quote(value, textfield=True)
                    # if we have an intra-word hyphen, we need quotes
                    if "\\-" in value or "\\+" in value:
                        if value[0] != '"':
                            value = '"%s"' % value
                else:
                    value = quote(value)
                if not value:  # don't search for empty strings, even quoted
                    continue
            elif isinstance(value, (int, float)):
                pass  # Do not raise an error for int or float values
            else:
                logger.info('skipping unsupported value "%r" (%s)', value, name)
                continue
            if name is None:
                if value and value[0] not in "+-":
                    value = "+%s" % value
            else:
                if name[0] not in "+-":
                    value = "+%s:%s" % (name, value)
                else:
                    value = "%s:%s" % (name, value)
            query[name] = value
        logger.debug('built query "%s"', query)

        if query:
            optimizeQueryParameters(query, params)
        return query, params
