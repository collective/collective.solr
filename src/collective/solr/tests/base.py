from plone.app.controlpanel.tests.cptc import ControlPanelTestCase
from Products.PloneTestCase import PloneTestCase as ptc
from Testing.testbrowser import Browser
from Testing.ZopeTestCase import Sandboxed

from collective.solr.tests.layer import layer
from collective.solr.utils import activate


ptc.setupPloneSite()


class SolrTestCase(Sandboxed, ptc.PloneTestCase):
    """ base class for integration tests """

    layer = layer


class SolrControlPanelTestCase(ControlPanelTestCase):
    """ base class for control panel tests """

    layer = layer


class SolrFunctionalTestCase(ptc.FunctionalTestCase):
    """ base class for functional tests """

    layer = layer

    def getBrowser(self, loggedIn=True):
        """ instantiate and return a testbrowser for convenience """
        browser = Browser()
        if loggedIn:
            user = ptc.default_user
            pwd = ptc.default_password
            browser.addHeader('Authorization', 'Basic %s:%s' % (user, pwd))
        return browser

    def setStatusCode(self, key, value):
        from ZPublisher import HTTPResponse
        HTTPResponse.status_codes[key.lower()] = value

    def activateAndReindex(self):
        """ activate solr indexing and reindex the existing content """
        activate()
        response = self.portal.REQUEST.RESPONSE
        original = response.write
        response.write = lambda x: x    # temporarily ignore output
        maintenance = self.portal.unrestrictedTraverse('@@solr-maintenance')
        maintenance.clear()
        maintenance.reindex()
        response.write = original
