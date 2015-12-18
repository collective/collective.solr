# -*- coding: utf-8 -*-

from plone.app.registry.browser import controlpanel

from collective.solr.interfaces import ISolrSchema, _





class SolrControlPanelForm(controlpanel.RegistryEditForm):

    id = "SolrControlPanel"
    label = _('label_solr_settings', default='Solr settings')
    schema = ISolrSchema
    schema_prefix = "collective.solr"

    def getAtomicUpdates(self):
        util = queryUtility(ISolrConnectionConfig)
        return getattr(util, 'atomic_updates', True)

    def setAtomicUpdates(self, value):
        util = queryUtility(ISolrConnectionConfig)
        if util is not None:
            util.atomic_updates = value

    atomic_updates = property(
        getAtomicUpdates, setAtomicUpdates)


class SolrControlPanel(controlpanel.ControlPanelFormWrapper):

    form = SolrControlPanelForm

