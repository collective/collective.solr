from unittest import TestCase

from collective.solr.dispatcher import solrSearchResults
from collective.solr.testing import (
    LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING,
    activateAndReindex,
)
from plone.app.testing import SITE_OWNER_NAME, SITE_OWNER_PASSWORD
from plone.uuid.interfaces import IUUID

try:
    from plone.testing.zope import Browser
except ImportError:
    from plone.testing.z2 import Browser

from transaction import commit
from ZODB.POSException import ConflictError
from zope import component
from zope.interface import Interface
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

UIDS = []


def raise_on_first_add(context, event):
    first = not bool(UIDS)
    UIDS.append(IUUID(context))
    if first:
        raise ConflictError()  # trigger a retry (once)


class ConflictTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        activateAndReindex(self.layer["portal"])
        commit()
        self.browser = Browser(self.layer["app"])
        self.browser.addHeader(
            "Authorization", "Basic %s:%s" % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD)
        )

    def test_retry_on_conflict(self):
        """This tests transaction handling when indexing in Solr, or more
        specifically properly aborting a transaction.  To do this we'll try to
        create some content and fake a `ConflictError` shortly before the
        transaction completes.  The publisher will catch it and retry, but
        while doing so the object will get a different UID than the first time.
        Without being able to abort the transaction Solr would receive two sets
        of data and consequently return two results when searching for this
        particular piece of content later on.
        """
        self.browser.open(self.layer["portal"].absolute_url())
        self.browser.getLink("Page").click()
        self.browser.getControl("Title", index=0).value = "Foo"
        component.provideHandler(raise_on_first_add, (Interface, IObjectCreatedEvent))
        self.browser.getControl("Save").click()
        self.assertEqual(len(UIDS), 2)
        self.assertEqual(len(solrSearchResults(SearchableText="Foo")), 1)

        sm = component.getSiteManager()
        sm.unregisterHandler(raise_on_first_add, (Interface, IObjectCreatedEvent))
