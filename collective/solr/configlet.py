from zope.component import adapts, queryUtility
from zope.formlib.form import FormFields
from zope.interface import implements
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.app.controlpanel.form import ControlPanelForm

from collective.solr.interfaces import ISolrSchema, _
from collective.solr.interfaces import ISolrConnectionConfig


class SolrControlPanelAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(ISolrSchema)

    def getActive(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'active', '')

    def setActive(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.active = value

    active = property(getActive, setActive)

    def getHost(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'host', '')

    def setHost(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.host = value

    host = property(getHost, setHost)

    def getPort(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'port', '')

    def setPort(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.port = value

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


class SolrControlPanel(ControlPanelForm):

    form_fields = FormFields(ISolrSchema)

    label = _('Solr settings')
    description = _('Settings to enable and configure Solr integration for Plone.')
    form_name = _('Solr settings')

