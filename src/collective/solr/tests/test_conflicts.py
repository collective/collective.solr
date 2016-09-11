from unittest import TestCase

from plone.app.contentlisting.interfaces import IContentListingObject
from plone.uuid.interfaces import IUUID
from zope.interface.verify import verifyClass

from collective.solr.contentlisting import FlareContentListingObject
from collective.solr.dispatcher import solrSearchResults
from collective.solr.flare import PloneFlare
from collective.solr.testing import activateAndReindex
from collective.solr.testing import HAS_PAC
from collective.solr.testing import LEGACY_COLLECTIVE_SOLR_FUNCTIONAL_TESTING
from plone import api
from plone.app.testing import SITE_OWNER_NAME
from plone.app.testing import SITE_OWNER_PASSWORD
from plone.app.testing import setRoles
from plone.testing.z2 import Browser
from transaction import commit
from ZODB.POSException import ConflictError
from zope import component
from zope.interface import implementer
from zope.interface import Interface
from zope.lifecycleevent.interfaces import IObjectCreatedEvent


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
        component.provideHandler(
            raise_on_first_add, (Interface, IObjectCreatedEvent,))

        self.browser.open(self.layer['portal'].absolute_url()) # + '/++add++Document')
        self.browser.getLink('Page').click()
        self.browser.getControl('Title').value = 'Foo'
        self.browser.getControl('Save').click()
  	self.assertEqual(len(UIDS), 2)
        self.assertEqual(len(solrSearchResults(SearchableText='Foo')), 1)

        sm = component.getSiteManager()
        sm.unregisterHandler(
            raise_on_first_add, (Interface, IObjectCreatedEvent,))
