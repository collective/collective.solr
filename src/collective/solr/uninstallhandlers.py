
from Products.CMFCore.utils import getToolByName
from Products.GenericSetup.utils import _resolveDottedName

def unregisterConfiglet(site):
    controlpanel = getToolByName(site, 'portal_controlpanel')
    controlpanel.unregisterConfiglet('SolrSettings')

UTILITIES = ((u"collective.solr.interfaces.ISolrConnectionConfig", u''),
        (u"collective.solr.interfaces.ISolrConnectionManager", u''),
        (u"collective.solr.interfaces.ISolrIndexQueueProcessor", u'solr'),)

def unregisterUtilities(site):
    sm = site.getSiteManager()
    for provided, name in UTILITIES:
        provided = _resolveDottedName(provided)
        if sm.queryUtility(provided, name) is not None:
            sm.unregisterUtility(provided=provided, name=name)

def uninstall(context):
    if context.readDataFile('collective-solr-uninstall.txt') is None:
        return
    site = context.getSite()
    unregisterConfiglet(site)
    unregisterUtilities(site)
