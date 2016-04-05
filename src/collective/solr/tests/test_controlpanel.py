# -*- coding: utf-8 -*-
import unittest2 as unittest

from plone.testing.z2 import Browser
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD

from zope.component import getUtility
from plone.registry.interfaces import IRegistry
from plone.registry import Registry
from collective.solr.interfaces import ISolrSchema

from zope.component import getMultiAdapter

from Products.CMFCore.utils import getToolByName

from plone.app.testing import TEST_USER_ID, setRoles

from collective.solr.testing import \
    COLLECTIVE_SOLR_INTEGRATION_TESTING

from collective.solr.testing import \
    COLLECTIVE_SOLR_FUNCTIONAL_TESTING


class SolrControlpanelIntegrationTest(unittest.TestCase):
    """Test that the solr settings are stored as plone.app.registry
    settings.
    """

    layer = COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

        self.registry = Registry()
        self.registry.registerInterface(ISolrSchema)

    def test_solr_controlpanel_view(self):
        view = getMultiAdapter((self.portal, self.portal.REQUEST),
                               name="solr-controlpanel")
        view = view.__of__(self.portal)
        self.assertTrue(view())

    def test_plone_app_registry_in_controlpanel(self):
        self.controlpanel = getToolByName(self.portal, "portal_controlpanel")
        self.assertTrue(
            'plone.app.registry' in [
                a.getAction(self)['id']
                for a in self.controlpanel.listActions()
            ]
        )

    def test_active_setting(self):
        self.assertTrue('active' in ISolrSchema.names())
        self.assertEqual(
            self.registry['collective.solr.interfaces.' +
                          'ISolrSchema.active'],
            False)

    def test_host_setting(self):
        self.assertTrue('host' in ISolrSchema.names())
        self.assertEqual(
            self.registry['collective.solr.interfaces.' +
                          'ISolrSchema.host'],
            u"127.0.0.1")

    def test_port_setting(self):
        self.assertTrue('port' in ISolrSchema.names())
        self.assertEqual(
            self.registry['collective.solr.interfaces.' +
                          'ISolrSchema.port'],
            8983)


class SolrControlPanelFunctionalTest(unittest.TestCase):
    """Test that changes in the solr control panel are actually
    stored in the registry.
    """

    layer = COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        self.app = self.layer['app']
        self.portal = self.layer['portal']
        self.portal_url = self.portal.absolute_url()
        self.browser = Browser(self.app)
        self.browser.handleErrors = False
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_solr_control_panel_link(self):
        self.browser.open(
            "%s/plone_control_panel" % self.portal_url)
        self.browser.getLink('Solr').click()

    def test_solr_control_panel_backlink(self):
        self.browser.open(
            "%s/@@solr-controlpanel" % self.portal_url)
        self.assertTrue("Plone Configuration" in self.browser.contents)

    def test_solr_control_panel_sidebar(self):
        self.browser.open(
            "%s/@@solr-controlpanel" % self.portal_url)
        self.browser.getLink('Site Setup').click()
        self.assertEqual(
            self.browser.url,
            'http://nohost/plone/@@overview-controlpanel')

    def test_active(self):
        self.browser.open(
            "%s/@@solr-controlpanel" % self.portal_url)
        self.browser.getControl('Active').selected = True
        self.browser.getControl('Save').click()

        registry = getUtility(IRegistry)
        settings = registry.forInterface(ISolrSchema)
        self.assertEqual(settings.active, True)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
