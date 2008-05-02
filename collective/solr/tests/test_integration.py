# integration and functional tests
# see http://plone.org/documentation/tutorial/testing/writing-a-plonetestcase-unit-integration-test
# for more information about the following setup

from unittest import TestSuite, makeSuite, main
from zope.testing.doctest import ELLIPSIS, NORMALIZE_WHITESPACE
from Testing.ZopeTestCase import FunctionalDocFileSuite
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup
from plone.app.controlpanel.tests.cptc import ControlPanelTestCase


@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    import collective.indexing
    zcml.load_config('configure.zcml', collective.indexing)
    import collective.solr
    zcml.load_config('configure.zcml', collective.solr)
    fiveconfigure.debug_mode = False

setup_product()
ptc.setupPloneSite(products=['collective.indexing', 'collective.solr'])


# test-specific imports go here...
from zope.component import queryUtility, getUtilitiesFor
from collective.indexing.interfaces import IIndexQueueProcessor
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.tests.utils import getData, fakehttp
from transaction import commit


class UtilityTests(ptc.PloneTestCase):

    def testGenericInterface(self):
        proc = queryUtility(IIndexQueueProcessor, name='solr')
        self.failUnless(proc, 'utility not found')
        self.failUnless(IIndexQueueProcessor.providedBy(proc))
        self.failUnless(ISolrIndexQueueProcessor.providedBy(proc))

    def testSolrInterface(self):
        proc = queryUtility(ISolrIndexQueueProcessor, name='solr')
        self.failUnless(proc, 'utility not found')
        self.failUnless(IIndexQueueProcessor.providedBy(proc))
        self.failUnless(ISolrIndexQueueProcessor.providedBy(proc))

    def testRegisteredProcessors(self):
        procs = list(getUtilitiesFor(IIndexQueueProcessor))
        self.failUnless(procs, 'no utilities found')
        solr = queryUtility(ISolrIndexQueueProcessor, name='solr')
        self.failUnless(solr in [util for name, util in procs], 'solr utility not found')


class IndexingTests(ptc.PloneTestCase):

    def afterSetUp(self):
        schema = getData('plone_schema.xml')
        self.proc = queryUtility(ISolrConnectionManager)
        self.proc.setHost(active=True)
        conn = self.proc.getConnection()
        fakehttp(conn, schema)          # fake schema response
        self.proc.getSchema()           # read and cache the schema

    def beforeTearDown(self):
        self.proc.closeConnection(clearSchema=True)
        self.proc.setHost(active=False)

    def testIndexObject(self):
        output = []
        connection = self.proc.getConnection()
        responses = getData('add_response.txt'), getData('commit_response.txt')
        output = fakehttp(connection, *responses)           # fake responses
        self.folder.processForm(values={'title': 'Foo'})    # updating sends data
        self.assertEqual(self.folder.Title(), 'Foo')
        self.assertEqual(str(output), '', 'reindexed unqueued!')
        commit()                        # indexing happens on commit
        required = '<field name="Title">Foo</field>'
        self.assert_(str(output).find(required) > 0, '"title" data not found')
        # due to the `commit()` above the changes from `afterSetUp`
        # need to be explicitly reversed...
        self.proc.setHost(active=False)
        commit()


def test_suite():
    return TestSuite([
        makeSuite(UtilityTests),
        makeSuite(IndexingTests),
        FunctionalDocFileSuite('configlet.txt',
            optionflags=ELLIPSIS | NORMALIZE_WHITESPACE,
            package='collective.solr.tests',
            test_class=ControlPanelTestCase),
    ])

if __name__ == '__main__':
    main(defaultTest='test_suite')

