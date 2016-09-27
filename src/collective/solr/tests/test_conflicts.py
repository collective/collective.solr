from unittest import TestCase

from plone.uuid.interfaces import IUUID

from collective.solr.dispatcher import solrSearchResults
from collective.solr.testing import activateAndReindex
from collective.solr.testing import HAS_PAC
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.testing.z2 import Browser
from transaction import commit
from ZODB.POSException import ConflictError
from zope import component
from zope.interface import Interface
from zope.lifecycleevent.interfaces import IObjectCreatedEvent

# override IObjectCreatedEvent for AT content
if not HAS_PAC:
    from Products.Archetypes.interfaces import IObjectInitializedEvent as IObjectCreatedEvent  # noqa


UIDS = []


def raise_on_first_add(context, event):
    first = not bool(UIDS)
    UIDS.append(IUUID(context))
    if first:
        raise ConflictError()   # trigger a retry (once)


class ConflictTests(TestCase):

    layer = LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING

    def setUp(self):
        activateAndReindex(self.layer['portal'])
        commit()
        self.browser = Browser(self.layer['app'])
        self.browser.addHeader(
            'Authorization',
            'Basic %s:%s' % (SITE_OWNER_NAME, SITE_OWNER_PASSWORD,)
        )

    def test_retry_on_conflict(self):
        self.browser.open(self.layer['portal'].absolute_url())
        self.browser.getLink('Page').click()
        self.browser.getControl('Title', index=0).value = 'Foo'
        component.provideHandler(
            raise_on_first_add, (Interface, IObjectCreatedEvent,))
        self.browser.getControl('Save').click()
        self.assertEqual(len(UIDS), 2)
        self.assertEqual(len(solrSearchResults(SearchableText='Foo')), 1)

        sm = component.getSiteManager()
        sm.unregisterHandler(
            raise_on_first_add, (Interface, IObjectCreatedEvent,))
