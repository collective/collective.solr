from unittest import defaultTestLoader
from zope.component import getUtility
from Products.GenericSetup.tests.common import TarballTester
from StringIO import StringIO

from collective.solr.tests.base import SolrTestCase
from collective.solr.interfaces import ISolrConnectionConfig


class SetupToolTests(SolrTestCase, TarballTester):

    def afterSetUp(self):
        config = getUtility(ISolrConnectionConfig)
        config.active = False
        config.host = 'foo'
        config.port = 23
        config.base = '/bar'

    def testImportStep(self):
        tool = self.portal.portal_setup
        result = tool.runImportStepFromProfile('profile-collective.solr:default', 'solr')
        self.assertEqual(result['steps'], [u'componentregistry', 'solr'])
        self.failUnless(result['messages']['solr'].endswith('collective.solr: settings imported.'))
        config = getUtility(ISolrConnectionConfig)
        self.assertEqual(config.active, False)
        self.assertEqual(config.host, 'localhost')
        self.assertEqual(config.port, 8983)
        self.assertEqual(config.base, '/solr')

    def testExportStep(self):
        tool = self.portal.portal_setup
        result = tool.runExportStep('solr')
        self.assertEqual(result['steps'], ['solr'])
        self.assertEqual(result['messages']['solr'], None)
        tarball = StringIO(result['tarball'])
        self._verifyTarballContents(tarball, ['solr.xml'])
        self._verifyTarballEntryXML(tarball, 'solr.xml', SOLR_XML)


SOLR_XML = """\
<?xml version="1.0"?>
<object name="solr">
  <connection>
    <active value="False" />
    <host value="foo" />
    <port value="23" />
    <base value="/bar" />
  </connection>
</object>
"""


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

