from Products.CMFCore.interfaces import IIndexQueueProcessor
from zope.interface import Interface
from zope.schema import Bool, Float, Int, List, Password, Text, TextLine
from zope.schema.interfaces import IVocabularyFactory

from collective.solr import SolrMessageFactory as _


# If we send too large a number to solr, it can't parse it
MAX_RESULTS_SUPPORTED_BY_SOLR = 1_000_000_000


class ISolrSchema(Interface):
    active = Bool(
        title=_("label_active", default="Active"),
        description=_(
            "help_active",
            default="Check this to enable the Solr integration, i.e. "
            "indexing and searching using the below settings.",
        ),
        default=False,
        required=False,
    )

    host = TextLine(
        title=_("label_host", default="Host"),
        description=_(
            "help_host", default="The host name of the Solr instance to be used."
        ),
    )

    port = Int(
        title=_("label_port", default="Port"),
        description=_("help_port", default="The port of the Solr instance to be used."),
    )

    solr_login = TextLine(
        title=_("login", default="Login"),
        description=_(
            "help_login", default="Authentication login of the SolR instance."
        ),
        required=False,
    )

    solr_password = Password(
        title=_("password", default="Password"),
        description=_(
            "help_password", default="Authentication password of the SolR instance."
        ),
        required=False,
    )

    base = TextLine(
        title=_("label_base", default="Base"),
        description=_(
            "help_base", default="The base prefix of the Solr instance to be used."
        ),
    )

    async_indexing = Bool(
        title=_("label_async", default="Asynchronous indexing"),
        default=False,
        required=False,
        description=_(
            "help_async",
            default="Check to enable asynchronous indexing operations, "
            "which will improve Zope response times in return for "
            "not having the Solr index updated immediately.",
        ),
    )

    auto_commit = Bool(
        title=_("label_auto_commit", default="Automatic commit"),
        default=True,
        required=False,
        description=_(
            "help_auto_commit",
            default="If enabled each index operation will cause a commit "
            "to be sent to Solr, which causes it to update its "
            "index. If you disable this, you need to configure "
            "commit policies on the Solr server side.",
        ),
    )

    commit_within = Int(
        title=_("label_commit_within", default="Commit within"),
        default=0,
        description=_(
            "help_commit_within",
            default="Maximum number of milliseconds after which adds "
            "should be processed by Solr. Defaults to 0, meaning "
            "immediate commits. Enabling this feature implicitly "
            "disables automatic commit and you should configure "
            "commit policies on the Solr server side. Otherwise "
            "large numbers of deletes without adds will not be "
            "processed. This feature requires a Solr 1.4 server.",
        ),
    )

    index_timeout = Float(
        title=_("label_index_timeout", default="Index timeout"),
        description=_(
            "help_index_timeout",
            default="Number of seconds after which an index request will "
            'time out. Set to "0" to disable timeouts.',
        ),
    )

    search_timeout = Float(
        title=_("label_search_timeout", default="Search timeout"),
        description=_(
            "help_search_timeout",
            default="Number of seconds after which a search request will "
            'time out. Set to "0" to disable timeouts.',
        ),
    )

    max_results = Int(
        title=_("label_max_results", default="Maximum search results"),
        description=_(
            "help_max_results",
            default="Specify the maximum number of matches to be returned "
            'when searching. Set to "10000000" or some other '
            "ridiculously large value that is higher than the "
            "possible number of rows that are expected.",
        ),
        default=1_000_000,
        max=MAX_RESULTS_SUPPORTED_BY_SOLR,
    )

    required = List(
        title=_("label_required", default="Required query parameters"),
        description=_(
            "help_required",
            default="Specify required query parameters, one per line. "
            "Searches will only get dispatched to Solr if any "
            "of the listed parameters is present in the query. "
            "Leave empty to dispatch all searches.",
        ),
        value_type=TextLine(),
        default=[],
        missing_value=[],
        required=False,
    )

    search_pattern = Text(
        title=_("label_search_pattern", default="Pattern for simple search queries"),
        description=_(
            "help_search_pattern",
            default="Specify a query pattern used for simple queries "
            "consisting only of words and numbers, i.e. not "
            "using any of Solr's advanced query expressions. "
            "{value} and {base_value} are available in the "
            "pattern and will be replaced by the search word "
            "and the search word stripped of wildcard symbols.",
        ),
    )

    prefix_wildcard = Bool(
        title=_(
            "label_simple_search_prefix_wildcard",
            default="Allow prefix wildcard searches and use them in simple searches",
        ),
        default=False,
        required=False,
    )

    force_simple_search = Bool(
        title=_("label_force_simple_search", default="Force simple search pattern"),
        description=_(
            "help_force_simple_search",
            default="If set all queries in SearchableText will use the "
            '"Pattern for simple search queries". This will remove all special '
            "solr characters and operators from the query text.",
        ),
        default=False,
        required=False,
    )

    allow_complex_search = Bool(
        title=_("allow_complex_search", default="Allow complex search"),
        description=_(
            "help_allow_complex_search",
            default="Allow a complex search in SearchableText by either prefixing the "
            'search text with "solr:" or passing "solr_complex_search" as a field '
            "in the catalog query.",
        ),
        default=False,
        required=False,
    )

    facets = List(
        title=_("label_facets", default="Default search facets"),
        description=_(
            "help_facets",
            default="Specify catalog indexes that should be queried for "
            "facet information, one per line.",
        ),
        value_type=TextLine(),
        default=[],
        required=False,
    )

    filter_queries = List(
        title=_("label_filter_queries", default="Filter query parameters"),
        description=_(
            "help_filter_queries",
            default="Specify query parameters for which filter queries "
            "should be used, one per line.  You can use several "
            "indices in one filter query separated by space. "
            "Typical examples are "
            '"effective expires allowedRolesAndUsers" or '
            '"review_state portal_type".',
        ),
        value_type=TextLine(),
        default=[],
        required=False,
    )

    slow_query_threshold = Int(
        title=_("label_slow_query_threshold", default="Slow query threshold"),
        description=_(
            "help_slow_query_threshold",
            default="Specify a threshold (in milliseconds) after which "
            "queries are considered to be slow causing them to "
            'be logged. Set to "0" to prevent any logging.',
        ),
        default=0,
    )

    effective_steps = Int(
        title=_("label_effective_steps", default="Effective date steps"),
        default=1,
        description=_(
            "help_effective_steps",
            default="Specify the effective date steps in seconds. "
            "Using 900 seconds (15 minutes) means the effective "
            "date sent to Solr changes every 15 minutes.",
        ),
    )

    exclude_user = Bool(
        title=_("label_exclude_user", default="Exclude user from allowedRolesAndUsers"),
        description=_(
            "help_exclude_user",
            default="Specify whether the user:userid should be excluded "
            "from allowedRolesAndUsers to improve cacheability "
            "on the expense of finding content with local roles"
            "given to specific users.",
        ),
        default=False,
        required=False,
    )

    highlight_fields = List(
        title=_("label_highlight_fields", "Highlighting fields"),
        description=_(
            "help_highlight_fields",
            default=(
                "Fields that should be used for highlighting. "
                "Snippets of text will be generated from the contents "
                "of these fields, with the search keywords that "
                "matched highlighted inside the text."
            ),
        ),
        value_type=TextLine(),
        default=[],
        required=False,
    )

    highlight_formatter_pre = TextLine(
        title=_("label_highlight_formatter_pre", default="Highlight formatter: pre"),
        description=_(
            "help_highlight_formatter_pre",
            default="The text to insert before the highlighted keyword.",
        ),
        default="[",
        required=False,
    )

    highlight_formatter_post = TextLine(
        title=_("label_highlight_formatter_post", default="Highlight formatter: post"),
        description=_(
            "help_highlight_formatter_post",
            default="The text to insert after the highlighted keyword.",
        ),
        default="]",
        required=False,
    )

    highlight_fragsize = Int(
        title=_("label_highlight_fragsize", default="Highlight Fragment Size"),
        description=_(
            "help_highlight_fragsize",
            default=(
                "The size, in characters, of the snippets (aka "
                "fragments) created by the highlighter."
            ),
        ),
        default=100,
    )

    field_list = List(
        title=_("label_field_list", default="Default fields to be returned"),
        description=_(
            "help_field_list",
            default=(
                "Specify metadata fields that should be returned for "
                "items in the result set, one per line. Defaults to "
                "all available plus ranking score."
            ),
        ),
        value_type=TextLine(),
        default=[],
        required=False,
    )

    levenshtein_distance = Float(
        title=_("label_levenshtein_distance", default="Levenshtein distance"),
        description=_(
            "help_levenshtein_distance",
            default="The Levenshtein distance is a string metric for "
            "measuring the difference between two strings. It allows"
            "you to perform fuzzy searches by specifying a value "
            "between 0 and 1.",
        ),
        required=False,
        default=0.0,
    )

    atomic_updates = Bool(
        title=_("label_atomic_updates", default="Enable atomic updates"),
        description=_(
            "help_atomic_updates",
            default="Atomic updates allows you to update only specific "
            'indexes, like "reindexObject(idxs=["portal_type"])".'
            "Unfortunately atomic updates are not compatible with "
            "index time boosting. If you enable atomic updates, "
            "index time boosting no longer works.",
        ),
        default=True,
        required=False,
    )

    boost_script = Text(
        title=_(
            "label_boost_script", default="Python script for custom index boosting"
        ),
        required=False,
        default="",
        missing_value="",
        description=_(
            "help_boost_script",
            default="This script is meant to be customized according to "
            "site-specific search requirements, e.g. boosting "
            'certain content types like "news items", ranking older '
            "content lower, consider special important content items,"
            " content rating etc."
            " the indexing data that will be sent to Solr is passed "
            "in as the `data` parameter, the indexable object is "
            "available via the `context` binding. The return value "
            "should be a dictionary consisting of field names and "
            "their respecitive boost values.  use an empty string "
            "as the key to set a boost value for the entire "
            "document/content item.",
        ),
    )

    use_tika = Bool(
        title=_("label_use_tika", default="Use Tika"),
        description=_(
            "help_use_tika",
            default="Upload binary files to Solr via Tika. "
            "That way Solr does not need direct access to the blob files on the file system. "
            "Use this setting when Solr runs on a separate server or if you use Relstorage instead of ZEO.",
        ),
        default=False,
        required=False,
    )

    tika_default_field = TextLine(
        title=_("label_tika_default_field", default="Tika default field"),
        description=_(
            "help_tika_default_field",
            default="Field that Tika uses to add the extracted text to.",
        ),
        default="content",
        required=False,
    )

    stopwords = Text(
        title=_("label_stopwords", default="Stopwords in the format of stopwords.txt"),
        description=_(
            "help_stopwords",
            default="Copy the stopwords.txt file here. "
            "Check Solr configuration to understand the format. - "
            "Stopwords will not get (word OR word*) simple "
            "expression, only (word). "
            "Notes: "
            "1. This will only work for multi word queries "
            "when force_simple_expression=True. - "
            "2. It's still necessary to filter stopwords from "
            "Solr, this option only causes the "
            "faulty (stopword*) parts removed from "
            "the expression ",
        ),
        default="",
        required=False,
    )

    stopwords_case_insensitive = Bool(
        title=_(
            "label_stopwords_case_insensitive", default="Stopwords are case insensitive"
        ),
        description=_(
            "help_stopwords_are_case_insensitive",
            default="Stopwords are case insensitive "
            "This depends on your Solr setup. If your stopwords are processed in a case insensitive way, "
            "this should be checked and it will apply the stopword wildcard removal in a case "
            "insensitive way.",
        ),
        default=False,
        required=False,
    )


class ISolrConnectionConfig(ISolrSchema):
    """utility to hold the connection configuration for the solr server"""


class IZCMLSolrConnectionConfig(Interface):
    """Solr connection settings configured through ZCML."""


class ISolrConnectionManager(Interface):
    """a thread-local connection manager for solr"""

    def setHost(active=False, host="localhost", port=8983, base="/solr/plone"):
        """set connection parameters"""

    def closeConnection(clearSchema=False):
        """close the current connection, if any"""

    def getConnection():
        """returns an existing connection or opens one"""

    def getSchema():
        """returns the currently used schema or fetches it.
        If the schema cannot be fetched None is returned."""

    def setTimeout(timeout, lock=object()):
        """set the timeout on the current (or to be opened) connection
        to the given value and optionally lock it until explicitly
        freed again"""

    def setIndexTimeout():
        """set the timeout on the current (or to be opened) connection
        to the value specified for indexing operations"""

    def setSearchTimeout():
        """set the timeout on the current (or to be opened) connection
        to the value specified for search operations"""


class ISolrIndexQueueProcessor(IIndexQueueProcessor):
    """an index queue processor for solr"""


class ISolrFlare(Interface):
    """a sol(a)r brain, i.e. a data container for search results"""


class IFlare(Interface):
    """marker interface for pluggable brain wrapper classes, providing
    additional helper methods like `getURL` etc"""


class ISearch(Interface):
    """a generic search interface
    FIXME: this should be defined in a generic package"""

    def search(query, **parameters):
        """perform a search with the given querystring and extra parameters
        (see http://wiki.apache.org/solr/CommonQueryParameters)"""

    def __call__(query, **parameters):
        """convenience alias for `search`"""

    def buildQueryAndParameters(default=None, **args):
        """helper to build a query for simple use-cases; the query is
        returned as a dictionary which might be string-joined or
        passed to the `search` method as the `query` argument,
        additionally search parameters are substracted from the
        args and returned as a separate dict"""


class ICatalogTool(Interface):
    """marker interface for plone's catalog tool"""


class ISearchDispatcher(Interface):
    """adapter for potentially dispatching a given query to an
    alternative search backend (instead of the portal catalog)"""

    def __call__(request, **keywords):
        """decide if an alternative search backend is capable of performing
        the given query and use it or fall back to the portal catalog"""


class ISolrMaintenanceView(Interface):
    """solr maintenance view for clearing, re-indexing content etc"""

    def optimize():
        """optimize solr indexes"""

    def clear():
        """clear all data from solr, i.e. delete all indexed objects"""

    def reindex(batch=1000, skip=0):
        """find all contentish objects (meaning all objects derived from one
        of the catalog mixin classes) and (re)indexes them"""

    def sync(batch=1000):
        """sync the solr index with the portal catalog;  records contained
        in the catalog but not in solr will be indexed and records not
        contained in the catalog can be optionally removed;  this can
        be used to ensure consistency between zope and solr after the
        solr server has been unavailable etc"""

    def cleanup(batch=1000):
        """remove entries from solr that don't have a corresponding Zope
        object  or have a different UID than the real object"""


class ISolrAddHandler(Interface):
    """An adder for solr documents"""


class IFacetTitleVocabularyFactory(IVocabularyFactory):
    """A vocabulary factory used to create a vocabulary that provides titles
    for facet values

    When facet values are displayed for selection on the search results page, a
    named IFacetTitleVocabularyFactory is looked up, and if it exists it's
    called to return a zope.schema.IBaseVocabulary vocabulary. The name is the
    same as the facet name (e.g. "portal_type" or "review_state"). This
    vocabulary should return zope.schema.ITitledTokenizedTerm items, their
    title attribute is what is displayed in the UI.
    """


class ICheckIndexable(Interface):
    """Check if an object is indexable"""

    def __call__():
        """Return `True`, if context is indexable and `False`otherwise"""
