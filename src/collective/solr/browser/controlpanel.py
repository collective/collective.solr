from collective.solr.interfaces import ISolrSchema
from collective.solr import SolrMessageFactory as _
from plone.app.registry.browser import controlpanel


class SolrControlpanelEditForm(controlpanel.RegistryEditForm):

    schema = ISolrSchema
    label = _(u"Solr settings")
    description = _(u"""Settings to enable and configure Solr integration.""")

    def updateFields(self):
        super(SolrControlpanelEditForm, self).updateFields()

    def updateWidgets(self):
        super(SolrControlpanelEditForm, self).updateWidgets()


class SolrControlpanel(controlpanel.ControlPanelFormWrapper):
    form = SolrControlpanelEditForm
