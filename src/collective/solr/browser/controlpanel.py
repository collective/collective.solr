# -*- coding: utf-8 -*-
from plone.app.registry.browser import controlpanel

try:
    from plone.protect.interfaces import IDisableCSRFProtection

    PLONE_PROTECT_INSTALLED = True
except ImportError:
    PLONE_PROTECT_INSTALLED = False
from collective.solr.interfaces import ISolrSchema, _
from Products.CMFPlone.utils import safe_unicode
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from Products.PythonScripts.PythonScript import PythonScript
from zope.interface import alsoProvides


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
            if PLONE_PROTECT_INSTALLED:
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
        if PLONE_PROTECT_INSTALLED:
            alsoProvides(self.request, IDisableCSRFProtection)
        portal[self.boost_script_id].write(boost_script)
        return changes


class SolrControlPanel(controlpanel.ControlPanelFormWrapper):

    form = SolrControlPanelForm
    index = ViewPageTemplateFile("controlpanel.pt")
