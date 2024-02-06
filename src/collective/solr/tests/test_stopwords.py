from unittest import TestCase

from zope.component import getGlobalSiteManager, provideUtility

from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.testing import COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE
from collective.solr.utils import getConfig
from collective.solr.stopword import isStopWord
import collective.solr.stopword
from unittest import mock


@mock.patch("collective.solr.stopword.raw", None)
@mock.patch("collective.solr.stopword.raw_case_insensitive", None)
@mock.patch("collective.solr.stopword.cooked", None)
class StopwordsUtilTests(TestCase):
    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def setUp(self):
        self.config = getConfig()
        self.config.force_simple_search = True
        self.config.stopwords_case_insensitive = False
        self.config.stopwords = """stopone
stoptwo
"""
        provideUtility(self.config, ISolrConnectionConfig)

    def tearDown(self):
        gsm = getGlobalSiteManager()
        gsm.unregisterUtility(self.config, ISolrConnectionConfig)

    def testIsStopword(self):
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertTrue(isStopWord("stoptwo", self.config))
        self.assertFalse(isStopWord("stopthree", self.config))

    def testCachingPreserves(self):
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertTrue(isStopWord("stoptwo", self.config))
        self.assertFalse(isStopWord("stopthree", self.config))
        collective.solr.stopword.cooked = ["stopone", "stopthree"]
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertFalse(isStopWord("stoptwo", self.config))
        self.assertTrue(isStopWord("stopthree", self.config))

    def testCachingUpdates(self):
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertTrue(isStopWord("stoptwo", self.config))
        self.assertFalse(isStopWord("stopthree", self.config))
        self.config.stopwords = """stopone
stopthree
"""
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertFalse(isStopWord("stoptwo", self.config))
        self.assertTrue(isStopWord("stopthree", self.config))

    def testCachingCaseInsensitivityUpdates(self):
        self.config.stopwords = """Stopone
Stoptwo
"""
        self.config.stopwords_case_insensitive = True
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertTrue(isStopWord("stoptwo", self.config))
        self.assertFalse(isStopWord("stopthree", self.config))
        self.config.stopwords_case_insensitive = False
        self.assertTrue(isStopWord("Stopone", self.config))
        self.assertTrue(isStopWord("Stoptwo", self.config))
        self.assertFalse(isStopWord("Stopthree", self.config))

    def testUnicode(self):
        self.config.stopwords = """für
daß
"""
        self.assertTrue(isStopWord("für", self.config))
        self.assertTrue(isStopWord("daß", self.config))

    def testCases(self):
        self.config.stopwords = """Uppercase
CamelCase
FULLCAPS
"""
        self.assertTrue(isStopWord("Uppercase", self.config))
        self.assertTrue(isStopWord("CamelCase", self.config))
        self.assertTrue(isStopWord("FULLCAPS", self.config))

    def testCaseInsensitive(self):
        self.config.stopwords = """Uppercase
CamelCase
FULLCAPS
"""
        self.config.stopwords_case_insensitive = True
        self.assertTrue(isStopWord("Uppercase", self.config))
        self.assertTrue(isStopWord("CamelCase", self.config))
        self.assertTrue(isStopWord("FULLCAPS", self.config))
        self.assertTrue(isStopWord("uppercase", self.config))
        self.assertTrue(isStopWord("camelcase", self.config))
        self.assertTrue(isStopWord("fullcaps", self.config))
        self.assertTrue(isStopWord("uppercasE", self.config))
        self.assertTrue(isStopWord("CAMELCASE", self.config))
        self.assertTrue(isStopWord("fullcaps", self.config))

    def testEmptyLines(self):
        self.config.stopwords = (
            """

stopone

"""
            + "   \n"
        )
        self.assertFalse(isStopWord("", self.config))
        self.assertFalse(isStopWord("   ", self.config))
        self.assertTrue(isStopWord("stopone", self.config))

    def testComments(self):
        self.config.stopwords = """stopone
stoptwo              | nostopone
| nostoptwo
stopthree            # nostopthree
# nostopfour
"""
        self.assertFalse(isStopWord("nostopone", self.config))
        self.assertFalse(isStopWord(" nostopone", self.config))
        self.assertFalse(isStopWord("nostoptwo", self.config))
        self.assertFalse(isStopWord(" nostoptwo", self.config))
        self.assertFalse(isStopWord("nostopthree", self.config))
        self.assertFalse(isStopWord(" nostopthree", self.config))
        self.assertFalse(isStopWord("nostopfour", self.config))
        self.assertFalse(isStopWord(" nostopfour", self.config))
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertTrue(isStopWord("stoptwo", self.config))
        self.assertTrue(isStopWord("stopthree", self.config))

    def testLeadingSpaces(self):
        # stopwords.txt does not allow leading spaces, but the registry
        # pads it up because of the way we define it in the xml.
        self.config.stopwords = (
            """
  stopone
    stoptwo
"""
            + "   \n"
        )
        self.assertFalse(isStopWord("", self.config))
        self.assertFalse(isStopWord("  ", self.config))
        self.assertFalse(isStopWord("    ", self.config))
        self.assertTrue(isStopWord("stopone", self.config))
        self.assertTrue(isStopWord("stoptwo", self.config))
