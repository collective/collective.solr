
from Products.CMFCore.utils import getToolByName

def uninstall(self):
    portal_setup = getToolByName(self, 'portal_setup')
    portal_setup.runAllImportStepsFromProfile(
            'profile-collective.solr:uninstall')
