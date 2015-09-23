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
from random import randint
from time import sleep
from zope.configuration import xmlconfig
import os
import subprocess
import sys
import urllib2
import socket

BUILDOUT_DIR = os.path.join(os.getcwd(), '..', '..', 'bin')


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
        if solr_port == 'RANDOM':
            solr_port = self._find_available_solr_port()

        self.solr_host = solr_host
        self.solr_port = solr_port
        self.solr_base = solr_base
        self.solr_url = 'http://{0}:{1}{2}'.format(
            solr_host,
            solr_port,
            solr_base
        )

    def _find_available_solr_port(self):
        for i in range(1 << 20):
            random_port = randint(1024, (1 << 16) - 1)
            try:
                a_socket = socket.socket(socket.AF_INET)
                a_socket.bind(('127.0.0.1', random_port))
                return random_port
            except socket.error:
                continue
            finally:
                a_socket.close()

    def setUp(self):
        """Start Solr and poll until it is up and running.
        """
        status = subprocess.check_output(['./solr-instance', 'status'],
                                         cwd=BUILDOUT_DIR)
        if status != 'Solr not running.\n':
            raise Exception("Sor is already running: %s", status)
        self.proc = subprocess.call(
            './solr-instance start -Djetty.port={0}'.format(self.solr_port),
            shell=True,
            close_fds=True,
            cwd=BUILDOUT_DIR
        )

        http_error = None
        waiting_time = 30.0
        time_step = 0.5
        running = False
        for i in range(int(waiting_time/time_step)):
            try:
                solr_ping_url = self.solr_url + '/admin/ping'
                result = urllib2.urlopen(solr_ping_url)
                if result.code == 200:
                    if '<str name="status">OK</str>' in result.read():
                        os.environ['SOLR_HOST'] = '{0}:{1}'.format(
                            self.solr_host, self.solr_port)
                        running = True
                        break
            except urllib2.URLError, http_error:
                sleep(time_step)
                sys.stdout.write('.')
        if not running:
            subprocess.call(
                './solr-instance stop',
                shell=True,
                close_fds=True,
                cwd=BUILDOUT_DIR
            )
            sys.stdout.write('Solr Instance could not be started !!!')
            raise Exception("Unable to start solr, %i %s", http_error.code,
                            http_error.msg)

    def tearDown(self):
        """Stop Solr.
        """
        subprocess.check_call(
            './solr-instance stop',
            shell=True,
            close_fds=True,
            cwd=BUILDOUT_DIR
        )

SOLR_FIXTURE = SolrLayer()


class CollectiveSolrLayer(PloneSandboxLayer, SolrLayer):
    """collective.solr test layer that fires up and shuts down a Solr instance
       together with Plone and collective.solr installed.
    """
    defaultBases = (PLONE_FIXTURE,)

    def __init__(
            self,
            bases=None,
            name='Collective Solr Layer',
            module=None,
            solr_active=False,
            solr_host='localhost',
            solr_port=8983,
            solr_base='/solr'):
        super(CollectiveSolrLayer, self).__init__(
            bases,
            name,
            module,
            solr_host=solr_host,
            solr_port=solr_port,
            solr_base=solr_base)
        self.solr_active = solr_active
        self.solr_url = 'http://{0}:{1}{2}'.format(
            self.solr_host,
            self.solr_port,
            self.solr_base
        )

    def setUp(self):
        """Call the setUp method of PloneSandboxLayer as well as the SolrLayer
           setUp method. We need both, the Plone/ZODB setup and Solr.
        """
        super(CollectiveSolrLayer, self).setUp()
        SolrLayer.setUp(self)

    def tearDown(self):
        """Call the tearDown method of PloneSandboxLayer as well as the
           SolrLayer tearDown method. We need both, the Plone/ZODB setup and
           Solr.
        """
        super(CollectiveSolrLayer, self).tearDown()
        SolrLayer.tearDown(self)

    def setUpZope(self, app, configurationContext):
        import collective.solr
        xmlconfig.file('configure.zcml',
                       collective.solr,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.solr:search')
        self.updateSolrSettings(portal)
        solr_settings = SolrControlPanelAdapter(portal)
        solr_settings.setActive(self.solr_active)
        solr_settings.setPort(self.solr_port)
        solr_settings.setBase(self.solr_base)

    def updateSolrSettings(self, portal):
        solr_settings = SolrControlPanelAdapter(portal)
        solr_settings.setActive(self.solr_active)
        solr_settings.setPort(self.solr_port)
        solr_settings.setBase(self.solr_base)

    def tearDownPloneSite(self, portal):
        solr_settings = SolrControlPanelAdapter(portal)
        solr_settings.setActive(False)
        solr_settings.setPort(self.solr_port)
        solr_settings.setBase('/solr')


class LegacyCollectiveSolrLayer(CollectiveSolrLayer):

    def setUpZope(self, app, configurationContext):
        super(LegacyCollectiveSolrLayer, self).setUpZope(
            app,
            configurationContext
        )
        import collective.indexing
        xmlconfig.file('configure.zcml',
                       collective.indexing,
                       context=configurationContext)
        installProduct(app, 'collective.indexing')

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
    response.write = lambda x: x    # temporarily ignore output
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
