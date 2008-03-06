# integration and functional tests
# see http://plone.org/documentation/tutorial/testing/writing-a-plonetestcase-unit-integration-test
# for more information about the following setup

from unittest import TestSuite, makeSuite, main
from Products.Five import zcml
from Products.Five import fiveconfigure
from Products.PloneTestCase import PloneTestCase as ptc
from Products.PloneTestCase.layer import onsetup


@onsetup
def setup_product():
    fiveconfigure.debug_mode = True
    import collective.indexing
    zcml.load_config('configure.zcml', collective.indexing)
    import collective.solr
    zcml.load_config('configure.zcml', collective.solr)
    fiveconfigure.debug_mode = False

setup_product()
ptc.setupPloneSite(products=['collective.solr'])


# test-specific imports go here...
from zope.component import queryUtility, getUtilitiesFor
from collective.indexing.interfaces import IIndexQueueProcessor
from collective.solr.interfaces import ISolrIndexQueueProcessor
from collective.solr.tests.test_solr import fakehttp
from collective.solr.tests.utils import getData


class TestCase(ptc.PloneTestCase):

    def testGenericInterface(self):
        proc = queryUtility(IIndexQueueProcessor)
        self.failUnless(proc, 'utility not found')
        self.failUnless(IIndexQueueProcessor.providedBy(proc))
        self.failUnless(ISolrIndexQueueProcessor.providedBy(proc))

    def testSolrInterface(self):
        proc = queryUtility(ISolrIndexQueueProcessor)
        self.failUnless(proc, 'utility not found')
        self.failUnless(IIndexQueueProcessor.providedBy(proc))
        self.failUnless(ISolrIndexQueueProcessor.providedBy(proc))

    def testRegisteredProcessors(self):
        procs = list(getUtilitiesFor(IIndexQueueProcessor))
        self.failUnless(procs, 'no utilities found')
        solr = queryUtility(ISolrIndexQueueProcessor)
        self.failUnless(solr in [util for name, util in procs], 'solr utility not found')

    def setupProcessor(self, schema='plone_schema.xml'):
        proc = queryUtility(ISolrIndexQueueProcessor)
        proc.setHost()
        conn = proc.getConnection()
        fakehttp(conn, getData(schema), []) # fake schema response
        proc.getSchema()                    # read and cache the schema
        return conn                         # return connection for faking requests

    def testIndexObject(self):
        output = []
        connection = self.setupProcessor()
        response = getData('add_response.txt')
        fakehttp(connection, response, output)              # fake add response
        self.folder.processForm(values={'title': 'Foo'})    # updating sends data
        self.assertEqual(self.folder.Title(), 'Foo')
        output = ''.join(output).replace('\r', '')
        required = '<field name="Title">Foo</field>'
        self.assert_(output.find(required) > 0, '"title" data not found')


def test_suite():
    return TestSuite([
        makeSuite(TestCase),
    ])

if __name__ == '__main__':
    main(defaultTest='test_suite')

