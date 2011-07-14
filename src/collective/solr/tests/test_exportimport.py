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
        config.auto_commit = True
        config.commit_within = 1000
        config.index_timeout = 7
        config.search_timeout = 3.1415
        config.max_results = 42
        config.required = ('foo', 'bar')
        config.search_pattern = 'foo:{value}'
        config.facets = ('type', 'state')
        config.filter_queries = ('type', )
        config.slow_query_threshold = 2342
        config.effective_steps = 900
        config.exclude_user = True

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
        self.assertEqual(config.auto_commit, True)
        self.assertEqual(config.commit_within, 1000)
        self.assertEqual(config.index_timeout, 0)
        self.assertEqual(config.search_timeout, 0)
        self.assertEqual(config.max_results, 0)
        self.assertEqual(config.required, ('SearchableText', ))
        self.assertEqual(config.facets, ('portal_type', 'review_state'))
        self.assertEqual(config.filter_queries, ('portal_type', ))
        self.assertEqual(config.slow_query_threshold, 0)
        self.assertEqual(config.effective_steps, 1)
        self.assertEqual(config.exclude_user, False)

    def testExportStep(self):
        tool = self.portal.portal_setup
        result = tool.runExportStep('solr')
        self.assertEqual(result['steps'], ['solr'])
        self.assertEqual(result['messages']['solr'], None)
        tarball = StringIO(result['tarball'])
        self._verifyTarballContents(tarball, ['solr.xml'])
        self._verifyTarballEntryXML(tarball, 'solr.xml', SOLR_XML)

    def testImportDoesntChangeActivationState(self):
        # re-applying the solr profile shouldn't change the activation state
        # so let's assume we've already got a site using the package...
        profile = 'profile-collective.solr:default'
        tool = self.portal.portal_setup
        result = tool.runImportStepFromProfile(profile, 'solr')
        self.assertEqual(result['steps'], [u'componentregistry', 'solr'])
        # by default solr support shouldn't be active
        config = getUtility(ISolrConnectionConfig)
        self.assertEqual(config.active, False)
        # so let's active and re-apply the profile...
        config.active = True
        result = tool.runImportStepFromProfile(profile, 'solr')
        self.assertEqual(result['steps'], [u'componentregistry', 'solr'])
        self.assertEqual(config.active, True)
        # now again in a deactivated state...
        config.active = False
        result = tool.runImportStepFromProfile(profile, 'solr')
        self.assertEqual(result['steps'], [u'componentregistry', 'solr'])
        self.assertEqual(config.active, False)


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
    <auto-commit value="True" />
    <commit-within value="1000" />
    <index-timeout value="7" />
    <search-timeout value="3.1415" />
    <max-results value="42" />
    <required-query-parameters>
      <parameter name="foo" />
      <parameter name="bar" />
    </required-query-parameters>
    <search-pattern value="foo:{value}" />
    <search-facets>
      <parameter name="type" />
      <parameter name="state" />
    </search-facets>
    <filter-query-parameters>
      <parameter name="type" />
    </filter-query-parameters>
    <slow-query-threshold value="2342" />
    <effective-steps value="900" />
    <exclude-user value="True" />
  </settings>
</object>
"""


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
