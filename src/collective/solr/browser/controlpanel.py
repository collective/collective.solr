# -*- coding: utf-8 -*-
from plone.app.registry.browser import controlpanel
from plone.protect.interfaces import IDisableCSRFProtection
from collective.solr.interfaces import ISolrSchema, _
from plone.restapi.controlpanels import RegistryConfigletPanel
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PythonScripts.PythonScript import PythonScript
from zope.component import adapter
from zope.interface import alsoProvides
from zope.interface import Interface


@adapter(Interface, Interface)
class SolrControlpanelAdapter(RegistryConfigletPanel):
    schema = ISolrSchema
    configlet_id = "SolrSettings"
    configlet_category_id = "Products"
    schema_prefix = "collective.solr"


class SolrControlPanelForm(controlpanel.RegistryEditForm):

    id = "SolrControlPanel"
    label = _("label_solr_settings", default="Solr settings")
    schema = ISolrSchema
    schema_prefix = "collective.solr"

    boost_script_id = "solr_boost_index_values"

    def getContent(self):
        content = super(SolrControlPanelForm, self).getContent()
        portal = self.context
        if self.boost_script_id in portal:
            boost_script = safe_unicode(portal[self.boost_script_id].read())
            # strip script metadata for display
            content.boost_script = "\n".join(
                [
                    line
                    for line in boost_script.splitlines()
                    if not line.startswith("##")
                ]
            )
            alsoProvides(self.request, IDisableCSRFProtection)
        return content

    def applyChanges(self, data):
        changes = super(SolrControlPanelForm, self).applyChanges(data)
        boost_script = data.get("boost_script", "")
        if "##parameters=data\n" not in boost_script:
            boost_script = "##parameters=data\n" + boost_script
        portal = self.context
        if self.boost_script_id not in self.context:
            # "special" documents get boosted during indexing...
            portal[self.boost_script_id] = PythonScript(self.boost_script_id)
        # since we create a PythonScript in ZODB we need to
        # disable CSRF protection
        alsoProvides(self.request, IDisableCSRFProtection)
        portal[self.boost_script_id].write(boost_script)
        return changes


class SolrControlPanel(controlpanel.ControlPanelFormWrapper):

    form = SolrControlPanelForm
    index = ViewPageTemplateFile("controlpanel.pt")
