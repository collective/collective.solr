# -*- coding: utf-8 -*-
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.app.testing import applyProfile
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting
from zope.configuration import xmlconfig


class CollectiveSolr(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        # Load ZCML
        import collective.solr
        xmlconfig.file('configure.zcml',
                       collective.solr,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.solr:default')
        setRoles(portal, TEST_USER_ID, ['Manager'])
        login(portal, TEST_USER_NAME)


COLLECTIVE_SOLR_FIXTURE = CollectiveSolr()
COLLECTIVE_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Integration")
COLLECTIVE_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Functional")
