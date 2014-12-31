from unittest import TestCase

from plone.app.contentlisting.interfaces import IContentListingObject
from zope.interface.verify import verifyClass

from collective.solr.contentlisting import FlareContentListingObject


class ContentListingTests(TestCase):

    def testInterfaceComplete(self):
        self.assertTrue(
            verifyClass(IContentListingObject, FlareContentListingObject))
