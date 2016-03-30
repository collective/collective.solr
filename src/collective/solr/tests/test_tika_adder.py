from unittest import TestCase, defaultTestLoader
from plone.namedfile.file import NamedBlobFile
from Products.Archetypes.interfaces import IBaseObject
from zope.interface import alsoProvides
from zope.component import queryAdapter
from plone.namedfile.tests.test_blobfile import registerUtilities
from collective.solr.interfaces import ISolrAddHandler
from collective.solr.testing import (
    COLLECTIVE_SOLR_INTEGRATION_TESTING
)


class BinaryAdderTests(TestCase):

    layer = COLLECTIVE_SOLR_INTEGRATION_TESTING

    def setUp(self):
        registerUtilities()

    def test_binary_archetypes(self):
        class MyField(object):

            content = NamedBlobFile('BLA')
            from Products.Archetypes import atapi
            content = atapi.FileField('ba')

            def get(self, context=None):
                return self.content

            def getPrimaryField(self):
                return self

        obj = MyField()
        alsoProvides(obj, IBaseObject)
        adder = queryAdapter(obj, ISolrAddHandler, 'File')
        adder.getpath()
        self.assertEqual(1, 2)


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)
