# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
from collective.solr.utils import activate
from plone.app.robotframework.testing import REMOTE_LIBRARY_BUNDLE_FIXTURE
from plone.app.testing import FunctionalTesting
from plone.app.testing import IntegrationTesting
try:  # pragma: no cover
    from plone.app.contenttypes.testing import PLONE_APP_CONTENTTYPES_FIXTURE as PLONE_FIXTURE  # noqa
    HAS_PAC = True
except ImportError:  # pragma: no cover
    from plone.app.testing.bbb import PTC_FIXTURE as PLONE_FIXTURE
    HAS_PAC = False
from plone.app.testing import PloneSandboxLayer
from plone.app.testing import TEST_USER_NAME
from plone.app.testing import applyProfile
from plone.app.testing import login
from plone.registry.interfaces import IRegistry
from plone.testing import Layer
from plone.testing import z2
from plone.testing.z2 import installProduct
from plone.api.portal import set_registry_record
from zope.interface import implementer
from zope.component import provideUtility
from time import sleep

import os
import sys
import urllib2
import subprocess
import pkg_resources

BIN_DIR = os.path.dirname(os.path.realpath(sys.argv[0]))

try:   # pragma: no cover
    pkg_resources.get_distribution('Products.LinguaPlone')
    HAS_LINGUAPLONE = True
except pkg_resources.DistributionNotFound:  # pragma: no cover
    HAS_LINGUAPLONE = False


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
            solr_host=u'localhost',
            solr_port=8983,
            solr_base=u'/solr',
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
        self.loadZCML(package=collective.indexing)
        import collective.solr
        self.loadZCML(package=collective.solr)
        installProduct(app, 'collective.indexing')

    def setUpPloneSite(self, portal):
        self.solr_layer.setUp()
        applyProfile(portal, 'collective.solr:default')
        set_registry_record('collective.solr.active', self.solr_active)
        set_registry_record('collective.solr.port', self.solr_port)
        set_registry_record('collective.solr.base', self.solr_base)

    def tearDownPloneSite(self, portal):
        set_registry_record('collective.solr.active', False)
        set_registry_record('collective.solr.port', 8983)
        set_registry_record('collective.solr.base', u'/solr')
        self.solr_layer.tearDown()


class LegacyCollectiveSolrLayer(CollectiveSolrLayer):

    def setUpPloneSite(self, portal):
        super(LegacyCollectiveSolrLayer, self).setUpPloneSite(portal)
        acl_users = getToolByName(portal, 'acl_users')
        acl_users.userFolderAddUser('user1', 'secret', ['Manager'], [])
        login(portal, 'user1')
        portal.portal_workflow.setDefaultChain('simple_publication_workflow')
        wfAction = portal.portal_workflow.doActionFor
        portal.invokeFactory('Document', id='front-page',
                             title='Welcome to Plone')
        portal.invokeFactory('Folder', id='events', title='EventsFolder')
        portal.invokeFactory('Folder', id='news', title='NewsFolder')
        portal.news.invokeFactory('Collection', id='aggregator', title='News')
        portal.events.invokeFactory('Collection', id='aggregator',
                                    title='Events')
        wfAction(portal['front-page'], 'publish')
        wfAction(portal.events, 'publish')
        wfAction(portal.news, 'publish')
        wfAction(portal.news.aggregator, 'publish')
        wfAction(portal.events.aggregator, 'publish')
        login(portal, TEST_USER_NAME)

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


@implementer(IRegistry)
class CollectiveSolrMockRegistry(object):

    def __init__(self):
        self.active = False
        self.host = u'localhost'
        self.port = None
        self.base = None
        self.async = False
        self.auto_commit = True
        self.commit_within = 0
        self.index_timeout = 0
        self.search_timeout = 0
        self.max_results = 0
        self.required = ()
        self.search_pattern = None
        self.facets = []
        self.filter_queries = ()
        self.slow_query_threshold = 0
        self.effective_steps = 1
        self.exclude_user = False
        self.field_list = []
        self.atomic_updates = False
        self.boost_script = u''

    def __getitem__(self, name):
        name_parts = name.split('.')
        return getattr(self, name_parts[2])

    def get(self, name, default=None):
        return

    def __setitem__(self, name, value):
        return

    def __contains__(self, name):
        return

    @property
    def records(self):
        return

    # Schema interface API

    def forInterface(self, interface, check=True, omit=(), prefix=None,
                     factory=None):
        return self

    def registerInterface(self, interface, omit=(), prefix=None):
        return

    def collectionOfInterface(self, interface, check=True, omit=(),
                              prefix=None, factory=None):
        return


class CollectiveSolrMockRegistryLayer(Layer):
    """Solr test layer that fires up and shuts down a Solr instance. This
       layer can be used to unit test a Solr configuration without having to
       fire up Plone.
    """

    def setUp(self):
        provideUtility(
            provides=IRegistry,
            component=CollectiveSolrMockRegistry(),
            name=u''
        )

    def tearDown(self):
        # XXX: we have to unregister the utility, otherwise the test fixture
        # will bleed into other tests. This currently makes a few unit tests
        # pass. We need to fix this properly before merging though. (timo)
        pass


def set_attributes(context, values):  # pragma: no cover
    if HAS_PAC:
        for key, value in values.iteritems():
            setattr(context, key, value)
    else:
        context.processForm(values=values)


COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE = CollectiveSolrMockRegistryLayer()

COLLECTIVE_SOLR_FIXTURE = CollectiveSolrLayer(solr_active=True)

COLLECTIVE_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Integration"
)

COLLECTIVE_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Functional"
)

COLLECTIVE_SOLR_ROBOT_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_SOLR_FIXTURE,
           REMOTE_LIBRARY_BUNDLE_FIXTURE,
           z2.ZSERVER_FIXTURE),
    name="CollectiveSolr:Acceptance"
)

LEGACY_COLLECTIVE_SOLR_INTEGRATION_TESTING = IntegrationTesting(
    bases=(LEGACY_COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Integration"
)

LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(LEGACY_COLLECTIVE_SOLR_FIXTURE,),
    name="CollectiveSolr:Functional"
)
