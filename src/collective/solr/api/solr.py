# most of the code here is a shameless copy from ftw.solr:
# https://github.com/4teamwork/ftw.solr/pull/162
from plone.restapi.search.handler import SearchHandler
from plone.restapi.search.utils import unflatten_dotted_dict
from plone.restapi.services import Service
from AccessControl.SecurityManagement import getSecurityManager
from collective.solr.interfaces import ISolrConnectionManager
from Products.CMFPlone.utils import base_hasattr
from zope.component import queryUtility
from zope.interface import implementer
from zope.interface import Interface
from collective.solr.interfaces import ISolrSchema
from plone.registry.interfaces import IRegistry
from six.moves import range
from zope.component import getUtility

import re
import six


class SolrSearchGet(Service):
    def reply(self):
        query = self.request.form.copy()
        query = unflatten_dotted_dict(query)
        return SearchHandler(self.context, self.request).search(query)


SPECIAL_CHARS = [
    "+",
    "-",
    "&&",
    "||",
    "!",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    "^",
    '"',
    "~",
    "*",
    "?",
    ":",
    "/",
]

OPERATORS = re.compile(r"(.*)\s+(AND|OR|NOT)\s+", re.UNICODE)


def escape(term):
    for char in SPECIAL_CHARS:
        term = term.replace(char, "\\" + char)
    return term


def is_simple_search(phrase):
    num_quotes = phrase.count('"')
    if num_quotes % 2 == 0:
        # Replace quoted parts with a marker
        # "foo bar" -> quoted
        parts = phrase.split('"')
        new_parts = []
        for i in range(0, len(parts)):
            if i % 2 == 0:
                new_parts.append(parts[i])
            else:
                new_parts.append("quoted")
        phrase = u"".join(new_parts)
    if bool(OPERATORS.match(phrase)):
        return False
    return True


def split_simple_search(phrase):
    parts = phrase.split('"')
    terms = []
    for i in range(0, len(parts)):
        if i % 2 == 0:
            # Unquoted text
            terms.extend([term for term in parts[i].split() if term])
        else:
            # The uneven parts are those inside quotes
            if parts[i]:
                terms.append('"%s"' % parts[i])
    return terms


def make_query(phrase):
    phrase = phrase.strip()
    if isinstance(phrase, six.binary_type):
        phrase = phrase.decode("utf8")
    registry = getUtility(IRegistry)
    settings = registry.forInterface(ISolrSchema)
    if is_simple_search(phrase):
        terms = split_simple_search(phrase)[:10]
        pattern = settings.simple_search_term_pattern
        term_queries = [pattern.format(term=escape(t)) for t in terms]
        if len(term_queries) > 1:
            term_queries = [u"(%s)" % q for q in term_queries]
        query = u" AND ".join(term_queries)
        if len(terms) > 1 or not phrase.isalnum():
            query = u"(%s) OR (%s)" % (
                settings.simple_search_phrase_pattern.format(phrase=escape(phrase)),
                query,
            )
    else:
        pattern = settings.complex_search_pattern
        query = pattern.format(phrase=phrase)
    if settings.local_query_parameters:
        query = settings.local_query_parameters + query
    return query


class ISolrSearch(Interface):
    """Solr search utility"""

    def search(
        request_handler=u"/select",
        query=u"*:*",
        filters=None,
        start=0,
        rows=1000,
        sort=None,
        **params
    ):
        """Perform a search with the given querystring and extra parameters"""


@implementer(ISolrSearch)
class SolrSearch(object):
    """A search utility for Solr"""

    def __init__(self):
        self._manager = None

    @property
    def manager(self):
        if self._manager is None:
            self._manager = queryUtility(ISolrConnectionManager)
        return self._manager

    def search(
        self,
        request_handler=u"/select",
        query=u"*:*",
        filters=None,
        start=0,
        rows=1000,
        sort=None,
        **params
    ):
        conn = self.manager.connection
        params = {u"params": params}
        params[u"query"] = query
        params[u"offset"] = start
        params[u"limit"] = rows
        if sort is not None:
            params[u"sort"] = sort
        if filters is None:
            filters = []
        if not isinstance(filters, list):
            filters = [filters]
        filters.insert(0, self.security_filter())
        params[u"filter"] = filters
        return conn.search(params, request_handler=request_handler)

    def security_filter(self):
        user = getSecurityManager().getUser()
        roles = user.getRoles()
        if "Anonymous" in roles:
            return u"allowedRolesAndUsers:Anonymous"
        roles = list(roles)
        roles.append("Anonymous")
        if base_hasattr(user, "getGroups"):
            groups = [u"user:%s" % x for x in user.getGroups()]
            if groups:
                roles = roles + groups
        roles.append(u"user:%s" % user.getId())
        # Roles with spaces need to be quoted
        roles = [u'"%s"' % escape(r) if " " in r else escape(r) for r in roles]
        return u"allowedRolesAndUsers:(%s)" % u" OR ".join(roles)
