# -*- coding: utf-8 -*-
from zope.component import adapts, queryUtility
from zope.formlib.form import FormFields
from zope.interface import implements
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.app.controlpanel.form import ControlPanelForm

from collective.solr.interfaces import ISolrSchema, _
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.interfaces import ISolrConnectionManager


class SolrControlPanelAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(ISolrSchema)

    def reset(self):
        manager = queryUtility(ISolrConnectionManager)
        if manager is not None:
            manager.closeConnection()

    def getActive(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'active', '')

    def setActive(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.active = value
        self.reset()

    active = property(getActive, setActive)

    def getHost(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'host', '')

    def setHost(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.host = value
        self.reset()

    host = property(getHost, setHost)

    def getPort(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'port', '')

    def setPort(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.port = value
        self.reset()

    port = property(getPort, setPort)

    def getBase(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'base', '')

    def setBase(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.base = value

    base = property(getBase, setBase)

    def getAsync(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'async', '')

    def setAsync(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.async = value

    async = property(getAsync, setAsync)

    def getAutoCommit(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'auto_commit', '')

    def setAutoCommit(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.auto_commit = value

    auto_commit = property(getAutoCommit, setAutoCommit)

    def getCommitWithin(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'commit_within', '')

    def setCommitWithin(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.commit_within = value

    commit_within = property(getCommitWithin, setCommitWithin)

    def getIndexTimeout(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'index_timeout', '')

    def setIndexTimeout(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.index_timeout = value

    index_timeout = property(getIndexTimeout, setIndexTimeout)

    def getSearchTimeout(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'search_timeout', '')

    def setSearchTimeout(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.search_timeout = value

    search_timeout = property(getSearchTimeout, setSearchTimeout)

    def getMaxResults(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'max_results', '')

    def setMaxResults(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.max_results = value

    max_results = property(getMaxResults, setMaxResults)

    def getRequiredParameters(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'required', '')

    def setRequiredParameters(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.required = value

    required = property(getRequiredParameters, setRequiredParameters)

    def getSearchPattern(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'search_pattern', '')

    def setSearchPattern(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.search_pattern = value.encode('utf-8')

    search_pattern = property(getSearchPattern, setSearchPattern)

    def getDefaultFacets(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'facets', '')

    def setDefaultFacets(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.facets = value

    facets = property(getDefaultFacets, setDefaultFacets)

    def getFilterQueryParameters(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'filter_queries', '')

    def setFilterQueryParameters(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.filter_queries = value

    filter_queries = property(
        getFilterQueryParameters, setFilterQueryParameters)

    def getSlowQueryThreshold(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'slow_query_threshold', '')

    def setSlowQueryThreshold(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.slow_query_threshold = value

    slow_query_threshold = property(
        getSlowQueryThreshold, setSlowQueryThreshold)

    def getEffectiveSteps(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'effective_steps', '')

    def setEffectiveSteps(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.effective_steps = value

    effective_steps = property(getEffectiveSteps, setEffectiveSteps)

    def getExcludeUser(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'exclude_user', '')

    def setExcludeUser(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.exclude_user = value

    exclude_user = property(getExcludeUser, setExcludeUser)

    def getHighlightFields(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'highlight_fields', '')

    def setHighlightFields(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.highlight_fields = value

    highlight_fields = property(getHighlightFields, setHighlightFields)

    def getHighlightFormatterPre(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'highlight_formatter_pre', '')

    def setHighlightFormatterPre(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.highlight_formatter_pre = value

    highlight_formatter_pre = property(
        getHighlightFormatterPre, setHighlightFormatterPre)

    def getHighlightFormatterPost(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'highlight_formatter_post', '')

    def setHighlightFormatterPost(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.highlight_formatter_post = value

    highlight_formatter_post = property(
        getHighlightFormatterPost, setHighlightFormatterPost)

    def getHighlightFragsize(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'highlight_fragsize', '')

    def setHighlightFragsize(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.highlight_fragsize = value

    highlight_fragsize = property(getHighlightFragsize, setHighlightFragsize)

    def getFieldList(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'field_list', '')

    def setFieldList(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.field_list = value

    field_list = property(getFieldList, setFieldList)

    def getLevenshteinDistance(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'levenshtein_distance', '')

    def setLevenshteinDistance(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.levenshtein_distance = value

    levenshtein_distance = property(
        getLevenshteinDistance, setLevenshteinDistance)

    def getAtomicUpdates(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'atomic_updates', True)

    def setAtomicUpdates(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.atomic_updates = value

    atomic_updates = property(
        getAtomicUpdates, setAtomicUpdates)


class SolrControlPanel(ControlPanelForm):

    form_fields = FormFields(ISolrSchema)

    label = _('label_solr_settings', default='Solr settings')
    description = _(
        'help_solr_settings',
        default='Settings to enable and configure Solr integration.')
    form_name = _('label_solr_settings', default='Solr settings')
