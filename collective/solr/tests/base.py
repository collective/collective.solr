# integration and functional tests
# see http://plone.org/documentation/tutorial/testing/writing-a-plonetestcase-unit-integration-test
# for more information about the following setup

from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.Five.testbrowser import Browser
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from collective.solr.utils import activate


@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    import collective.indexing
    zcml.load_config('configure.zcml', collective.indexing)
    import collective.solr
    zcml.load_config('configure.zcml', collective.solr)
    fiveconfigure.debug_mode = False

setup_product()
ptc.setupPloneSite(extension_profiles=(
    'collective.indexing:default',
    'collective.solr:default',
    'collective.solr:search',
))


class SolrTestCase(ptc.PloneTestCase):
    """ base class for integration tests """


class SolrFunctionalTestCase(ptc.FunctionalTestCase):
    """ base class for functional tests """

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

