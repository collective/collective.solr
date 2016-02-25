# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from collective.solr.configlet import SolrControlPanelAdapter
from collective.solr.utils import activate
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_ID
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.app.testing import setRoles
from plone.testing import Layer
from plone.testing.z2 import installProduct
from time import sleep
from zope.configuration import xmlconfig

import os
import sys
import urllib2
import subprocess

BIN_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))


class SolrLayer(Layer):
    """Solr test layer that fires up and shuts down a Solr instance. This
       layer can be used to unit test a Solr configuration without having to
       fire up Plone.
    """
    proc = None

    def __init__(
            self,
            bases=None,
            name='Solr Layer',
            module=None,
            solr_host='localhost',
            solr_port=8983,
            solr_base='/solr'):
        super(SolrLayer, self).__init__(bases, name, module)
        self.solr_host = solr_host
        self.solr_port = solr_port
        self.solr_base = solr_base
        self.solr_url = 'http://{0}:{1}{2}'.format(
            solr_host,
            solr_port,
            solr_base
        )

    def setUp(self):
        """Start Solr and poll until it is up and running.
        """
        self.proc = subprocess.call(
            './solr-instance start',
            shell=True,
            close_fds=True,
            cwd=BIN_DIR
        )
        # Poll Solr until it is up and running
        solr_ping_url = '{0}/admin/ping'.format(self.solr_url)
        for i in range(1, 10):
            try:
                result = urllib2.urlopen(solr_ping_url)
                if result.code == 200:
                    if '<str name="status">OK</str>' in result.read():
                        break
            except urllib2.URLError:
                sleep(3)
                sys.stdout.write('.')
            if i == 9:
                subprocess.call(
                    './solr-instance stop',
                    shell=True,
                    close_fds=True,
                    cwd=BIN_DIR
                )
                sys.stdout.write('Solr Instance could not be started !!!')

    def tearDown(self):
        """Stop Solr.
        """
        subprocess.check_call(
            './solr-instance stop',
            shell=True,
            close_fds=True,
            cwd=BIN_DIR
        )


SOLR_FIXTURE = SolrLayer()


class CollectiveSolrLayer(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE, )

    def __init__(
            self,
            bases=None,
            name='Collective Solr Layer',
            module=None,
            solr_host='localhost',
            solr_port=8983,
            solr_base='/solr',
            solr_active=False):
        super(PloneSandboxLayer, self).__init__(bases, name, module)
        self.solr_active = solr_active
        self.solr_host = solr_host
        self.solr_port = solr_port
        self.solr_base = solr_base
        # SolrLayer should use the same settings as CollectiveSolrLayer
        self.solr_layer = SolrLayer(
            bases,
            name,
            module,
            solr_host=solr_host,
            solr_port=solr_port,
            solr_base=solr_base
        )

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
        self.solr_layer.setUp()
        applyProfile(portal, 'collective.solr:search')
        solr_settings = SolrControlPanelAdapter(portal)
        solr_settings.setActive(self.solr_active)
        solr_settings.setPort(self.solr_port)
        solr_settings.setBase(self.solr_base)

    def tearDownPloneSite(self, portal):
        solr_settings = SolrControlPanelAdapter(portal)
        solr_settings.setActive(False)
        solr_settings.setPort(8983)
        solr_settings.setBase('/solr')
        self.solr_layer.tearDown()


class LegacyCollectiveSolrLayer(CollectiveSolrLayer):

    def setUpPloneSite(self, portal):
        super(LegacyCollectiveSolrLayer, self).setUpPloneSite(portal)
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

LEGACY_COLLECTIVE_SOLR_FIXTURE = LegacyCollectiveSolrLayer()


def activateAndReindex(portal):
    """ activate solr indexing and reindex the existing content """
    activate()
    response = portal.REQUEST.RESPONSE
    original = response.write
    response.write = lambda x: x  # temporarily ignore output
    maintenance = portal.unrestrictedTraverse('@@solr-maintenance')
    maintenance.clear()
    maintenance.reindex()
    response.write = original


COLLECTIVE_SOLR_FIXTURE = CollectiveSolrLayer()

COLLECTIVE_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LEGACY_COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Integration"
)

COLLECTIVE_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(LEGACY_COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Functional"
)
