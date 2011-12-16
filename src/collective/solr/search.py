from logging import getLogger
from time import time
from zope.interface import implements
from zope.component import queryUtility
from Missing import MV

from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISearch
from collective.solr.parser import SolrResponse
from collective.solr.exceptions import SolrInactiveException
from collective.solr.queryparser import quote
from collective.solr.utils import isWildCard
from collective.solr.utils import prepare_wildcard


logger = getLogger('collective.solr.search')


class Search(object):
    """ a search utility for solr """
    implements(ISearch)

    def __init__(self):
        self.manager = None

    def getManager(self):
        if self.manager is None:
            self.manager = queryUtility(ISolrConnectionManager)
        return self.manager

    def search(self, query, **parameters):
        """ perform a search with the given querystring and parameters """
        start = time()
        config = queryUtility(ISolrConnectionConfig)
        manager = self.getManager()
        manager.setSearchTimeout()
        connection = manager.getConnection()
        if connection is None:
            raise SolrInactiveException
        if not 'rows' in parameters:
            parameters['rows'] = config.max_results or ''
            logger.info('falling back to "max_results" (%d) without a "rows" '
                'parameter: %r (%r)', config.max_results, query, parameters)
        if isinstance(query, dict):
            query = ' '.join(query.values())
        logger.debug('searching for %r (%r)', query, parameters)
        if 'sort' in parameters:    # issue warning for unknown sort indices
            index, order = parameters['sort'].split()
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
            logger.info('slow query: %d/%d ms for %r (%r)',
                results.responseHeader['QTime'], elapsed, query, parameters)
        return results

    __call__ = search

    def buildQuery(self, default=None, **args):
        """ helper to build a querystring for simple use-cases """
        logger.debug('building query for "%r", %r', default, args)
        schema = self.getManager().getSchema() or {}
        defaultSearchField = getattr(schema, 'defaultSearchField', None)
        args[None] = default
        query = {}
        for name, value in sorted(args.items()):
            field = schema.get(name or defaultSearchField, None)
            if field is None or not field.indexed:
                logger.warning('dropping unknown search attribute "%s" '
                    ' (%r) for query: %r', name, value, args)
                continue
            if isinstance(value, bool):
                value = str(value).lower()
            elif not value:     # solr doesn't like empty fields (+foo:"")
                continue
            elif field.class_ == 'solr.BoolField':
                if not isinstance(value, (tuple, list)):
                    value = [value]
                falses = '0', 'False', MV
                true = lambda v: bool(v) and v not in falses
                value = set(map(true, value))
                if not len(value) == 1:
                    assert len(value) == 2      # just to make sure
                    continue                    # skip when "true or false"
                value = str(value.pop()).lower()
            elif isinstance(value, (tuple, list)):
                # list items should be treated as literals, but
                # nevertheless only get quoted when necessary
                def quoteitem(term):
                    if isinstance(term, unicode):
                        term = term.encode('utf-8')
                    quoted = quote(term)
                    if not quoted.startswith('"') and not quoted == term:
                        quoted = quote('"' + term + '"')
                    return quoted
                value = '(%s)' % ' OR '.join(map(quoteitem, value))
            elif isinstance(value, set):        # sets are taken literally
                if len(value) == 1:
                    query[name] = ''.join(value)
                else:
                    query[name] = '(%s)' % ' OR '.join(value)
                continue
            elif isinstance(value, basestring):
                if field.class_ == 'solr.TextField':
                    if isWildCard(value):
                        value = prepare_wildcard(value)
                    value = quote(value, textfield=True)
                    # if we have an intra-word hyphen, we need quotes
                    if '\\-' in value or '\\+' in value:
                        if value[0] != '"':
                            value = '"%s"' % value
                else:
                    value = quote(value)
                if not value:   # don't search for empty strings, even quoted
                    continue
            else:
                logger.info('skipping unsupported value "%r" (%s)',
                    value, name)
                continue
            if name is None:
                if value and value[0] not in '+-':
                    value = '+%s' % value
            else:
                value = '+%s:%s' % (name, value)
            query[name] = value
        logger.debug('built query "%s"', query)
        return query
