from zope.interface import Interface
from zope.component import adapts, queryUtility
from zope.formlib.form import FormFields
from zope.interface import implements
from zope.schema import Bool, TextLine, Int
from Products.CMFDefault.formlib.schema import SchemaAdapterBase
from Products.CMFPlone import PloneMessageFactory as _
from Products.CMFPlone.interfaces import IPloneSiteRoot
from plone.app.controlpanel.form import ControlPanelForm
from collective.solr.interfaces import ISolrConnectionManager


class ISolrSchema(Interface):

    active = Bool(title=_(u'Active'), default=False,
        description=_(u'Check this to enable the Solr integration, i.e. '
                       'indexing and searching using the below settings.'))

    host = TextLine(title=_(u'Host'),
        description=_(u'The host name of the Solr instance to be used.'))

    port = Int(title=_(u'Port'),
        description=_(u'The port of the Solr instance to be used.'))

    base = TextLine(title=_(u'Base'),
        description=_(u'The base prefix of the Solr instance to be used.'))


class SolrControlPanelAdapter(SchemaAdapterBase):
    adapts(IPloneSiteRoot)
    implements(ISolrSchema)

    def getActive(self):
        util = queryUtility(ISolrConnectionManager)
        return getattr(util, 'active', '')

    def setActive(self, value):
        util = queryUtility(ISolrConnectionManager)
        if util is not None:
            util.active = value

    active = property(getActive, setActive)

    def getHost(self):
        util = queryUtility(ISolrConnectionManager)
        return getattr(util, 'host', '')

    def setHost(self, value):
        util = queryUtility(ISolrConnectionManager)
        if util is not None:
            util.host = value

    host = property(getHost, setHost)

    def getPort(self):
        util = queryUtility(ISolrConnectionManager)
        return getattr(util, 'port', '')

    def setPort(self, value):
        util = queryUtility(ISolrConnectionManager)
        if util is not None:
            util.port = value

    port = property(getPort, setPort)

    def getBase(self):
        util = queryUtility(ISolrConnectionManager)
        return getattr(util, 'base', '')

    def setBase(self, value):
        util = queryUtility(ISolrConnectionManager)
        if util is not None:
            util.base = value

    base = property(getBase, setBase)


class SolrControlPanel(ControlPanelForm):

    form_fields = FormFields(ISolrSchema)

    label = _('Solr settings')
    description = _('Settings to enable and configure Solr integration for Plone.')
    form_name = _('Solr settings')

