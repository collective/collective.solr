from unittest import TestCase, defaultTestLoader, main
from collective.solr.tests.utils import getData
from collective.solr.parser import SolrResponse
from collective.solr.browser.utils import convertFacets


class FacettingHelperTest(TestCase):

    def testConvertFacets(self):
        fields = dict(portal_type=dict(Document=10,
            Folder=3, Event=5, Topic=2))
        info = convertFacets(fields)
        # the info should consist of 1 dict with `field` and `counts` keys
        self.assertEqual([sorted(i) for i in info], [['counts', 'title']] * 1)
        # next let's check the field names
        self.assertEqual([i['title'] for i in info], ['portal_type'])
        # and the fields contents
        types, = info
        self.assertEqual(types['title'], 'portal_type')
        self.assertEqual(types['counts'], [
            dict(name='Document', count=10),
            dict(name='Event', count=5),
            dict(name='Folder', count=3),
            dict(name='Topic', count=2),
        ])

    def testConvertFacetResponse(self):
        response = SolrResponse(getData('facet_xml_response.txt'))
        fields = response.facet_counts['facet_fields']
        info = convertFacets(fields)
        # the info should consist of 2 dicts with `field` and `counts` keys
        self.assertEqual([sorted(i) for i in info], [['counts', 'title']] * 2)
        # next let's check the field names
        self.assertEqual([i['title'] for i in info], ['cat', 'inStock'])
        # and the fields contents
        cat, inStock = info
        self.assertEqual(cat['title'], 'cat')
        self.assertEqual(cat['counts'], [
            dict(name='search', count=1),
            dict(name='software', count=1),
            dict(name='electronics', count=0),
            dict(name='monitor', count=0),
        ])
        self.assertEqual(inStock['title'], 'inStock')
        self.assertEqual(inStock['counts'], [
            dict(name='true', count=1),
        ])


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')
