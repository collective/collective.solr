# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from collective.solr.utils import activate
from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.testing.z2 import installProduct
from zope.configuration import xmlconfig


class CollectiveSolr(PloneSandboxLayer):

    defaultBases = (PLONE_APP_CONTENTTYPES_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import collective.indexing
        xmlconfig.file('configure.zcml',
                       collective.indexing,
                       context=configurationContext)
        import collective.solr
        xmlconfig.file('configure.zcml',
                       collective.solr,
                       context=configurationContext)
        installProduct(app, 'collective.indexing')

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.solr:search')


class LegacyCollectiveSolr(CollectiveSolr):

    def setUpPloneSite(self, portal):
        super(LegacyCollectiveSolr, self).setUpPloneSite(portal)
        acl_users = getToolByName(portal, 'acl_users')
        acl_users.userFolderAddUser('user1', 'secret', ['Manager'], [])
        login(portal, 'user1')
        portal.portal_workflow.setDefaultChain('simple_publication_workflow')
        wfAction = portal.portal_workflow.doActionFor
        portal.invokeFactory('Folder', id='Members', title='Users')
        portal.invokeFactory('Document', id='front-page',
                             title='Welcome to Plone')
        portal.invokeFactory('Folder', id='events', title='EventsFolder')
        portal.invokeFactory('Folder', id='news', title='NewsFolder')
        portal.news.invokeFactory('Collection', id='aggregator', title='News')
        portal.events.invokeFactory('Collection', id='aggregator',
                                    title='Events')
        wfAction(portal.Members, 'publish')
        wfAction(portal['front-page'], 'publish')
        wfAction(portal.events, 'publish')
        wfAction(portal.news, 'publish')
        wfAction(portal.news.aggregator, 'publish')
        wfAction(portal.events.aggregator, 'publish')
        login(portal, TEST_USER_NAME)
        setRoles(portal, TEST_USER_ID, ['Manager'])
        portal.Members.invokeFactory('Folder', id='test_user_1_', title='')
        setRoles(portal, TEST_USER_ID, [])


def activateAndReindex(portal):
    """ activate solr indexing and reindex the existing content """
    activate()
    response = portal.REQUEST.RESPONSE
    original = response.write
    response.write = lambda x: x    # temporarily ignore output
    maintenance = portal.unrestrictedTraverse('@@solr-maintenance')
    maintenance.clear()
    maintenance.reindex()
    response.write = original

COLLECTIVE_SOLR_FIXTURE = CollectiveSolr()
LEGACY_COLLECTIVE_SOLR_FIXTURE = LegacyCollectiveSolr()
COLLECTIVE_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LEGACY_COLLECTIVE_SOLR_FIXTURE,),
    name='CollectiveSolr:Integration')
COLLECTIVE_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(LEGACY_COLLECTIVE_SOLR_FIXTURE,),
    name='CollectiveSolr:Functional')
