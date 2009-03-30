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
        config.async = False
        config.index_timeout = 7
        config.search_timeout = 3.1415
        config.max_results = 42
        config.required = ('foo', 'bar')
        config.facets = ('type', 'state')

    def testImportStep(self):
        profile = 'profile-collective.solr:default'
        tool = self.portal.portal_setup
        result = tool.runImportStepFromProfile(profile, 'solr')
        self.assertEqual(result['steps'], [u'componentregistry', 'solr'])
        output = 'collective.solr: settings imported.'
        self.failUnless(result['messages']['solr'].endswith(output))
        config = getUtility(ISolrConnectionConfig)
        self.assertEqual(config.active, False)
        self.assertEqual(config.host, '127.0.0.1')
        self.assertEqual(config.port, 8983)
        self.assertEqual(config.base, '/solr')
        self.assertEqual(config.async, False)
        self.assertEqual(config.index_timeout, 0)
        self.assertEqual(config.search_timeout, 0)
        self.assertEqual(config.max_results, 0)
        self.assertEqual(config.required, ('SearchableText', ))
        self.assertEqual(config.facets, ('type', 'state'))
        # importing the "facet" profile should also set them up...
        profile = 'profile-collective.solr:facets'
        result = tool.runImportStepFromProfile(profile, 'solr')
        self.assertEqual(config.facets, ('portal_type', 'review_state'))

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
  <settings>
    <async value="False" />
    <index-timeout value="7" />
    <search-timeout value="3.1415" />
    <max-results value="42" />
    <required-query-parameters>
      <parameter name="foo" />
      <parameter name="bar" />
    </required-query-parameters>
    <search-facets>
      <parameter name="type" />
      <parameter name="state" />
    </search-facets>
  </settings>
</object>
"""


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
