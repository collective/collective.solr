from unittest import TestCase, defaultTestLoader, main
from zope.component import provideUtility, getGlobalSiteManager
from collective.solr.tests.utils import getData
from collective.solr.interfaces import ISolrConnectionConfig
from collective.solr.manager import SolrConnectionConfig
from collective.solr.parser import SolrResponse
from collective.solr.browser.utils import facetParameters, convertFacets
from urllib import unquote


class Dummy(object):
    """ dummy class that allows setting attributes """


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
        self.assertEqual([(c['name'], c['count']) for c in types['counts']], [
            ('Document', 10),
            ('Event', 5),
            ('Folder', 3),
            ('Topic', 2),
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
        self.assertEqual([(c['name'], c['count']) for c in cat['counts']], [
            ('search', 1),
            ('software', 1),
            ('electronics', 0),
            ('monitor', 0),
        ])
        self.assertEqual(inStock['title'], 'inStock')
        self.assertEqual([(c['name'], c['count']) for c in inStock['counts']], [
            ('true', 1),
        ])

    def testFacetParameters(self):
        context = Dummy()
        request = {}
        # with nothing set up, no facets will be returned
        self.assertEqual(facetParameters(context, request), [])
        # setting up the regular config utility should give the default value
        cfg = SolrConnectionConfig()
        provideUtility(cfg, ISolrConnectionConfig)
        self.assertEqual(facetParameters(context, request), [])
        # so let's set it...
        cfg.facets = ['foo']
        self.assertEqual(facetParameters(context, request), ['foo'])
        # override the setting on the context
        context.facet_fields = ['bar']
        self.assertEqual(facetParameters(context, request), ['bar'])
        # and again via the request
        request['facet.field'] = ['foo', 'bar']
        self.assertEqual(facetParameters(context, request), ['foo', 'bar'])
        # clean up...
        getGlobalSiteManager().unregisterUtility(cfg, ISolrConnectionConfig)

    def testFacetLinks(self):
        context = Dummy()
        context.facet_fields = ['portal_type']
        request = {'foo': 'bar'}
        fields = dict(portal_type=dict(Document=10, Folder=3, Event=5))
        info = convertFacets(fields, context, request)
        # let's check queries for the one and only facet field
        self.assertEqual(len(info), 1)
        counts = info[0]['counts']
        self.assertEqual(len(counts), 3)
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(counts[0]['name'], 'Document')
        self.assertEqual(params(counts[0]['query']), [
            'foo=bar', 'fq=portal_type:Document'])
        self.assertEqual(counts[1]['name'], 'Event')
        self.assertEqual(params(counts[1]['query']), [
            'foo=bar', 'fq=portal_type:Event'])
        self.assertEqual(counts[2]['name'], 'Folder')
        self.assertEqual(params(counts[2]['query']), [
            'foo=bar', 'fq=portal_type:Folder'])

    def testFacetLinksWithSelectedFacet(self):
        context = Dummy()
        request = {'foo': 'bar', 'facet.field': 'bar'}
        fields = dict(foo=dict(private=2, published=4))
        info = convertFacets(fields, context, request)
        self.assertEqual(len(info), 1)
        counts = info[0]['counts']
        self.assertEqual(len(counts), 2)
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(counts[0]['name'], 'published')
        self.assertEqual(params(counts[0]['query']), [
            'facet.field=bar', 'foo=bar', 'fq=foo:published'])
        self.assertEqual(counts[1]['name'], 'private')
        self.assertEqual(params(counts[1]['query']), [
            'facet.field=bar', 'foo=bar', 'fq=foo:private'])

    def testFacetLinksWithMultipleFacets(self):
        context = Dummy()
        request = {'facet.field': ['foo', 'bar']}
        fields = dict(foo=dict(Document=10, Folder=3, Event=5),
            bar=dict(private=2, published=4))
        info = convertFacets(fields, context, request)
        self.assertEqual(len(info), 2)
        # check the facets for 'bar'
        bars = info[0]['counts']
        self.assertEqual(len(bars), 2)
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(params(bars[0]['query']), [
            'facet.field=foo', 'fq=bar:published'])
        self.assertEqual(params(bars[1]['query']), [
            'facet.field=foo', 'fq=bar:private'])
        # and also the one for 'foo'
        foos = info[1]['counts']
        self.assertEqual(len(foos), 3)
        self.assertEqual(params(foos[0]['query']), [
            'facet.field=bar', 'fq=foo:Document'])
        self.assertEqual(params(foos[1]['query']), [
            'facet.field=bar', 'fq=foo:Event'])
        self.assertEqual(params(foos[2]['query']), [
            'facet.field=bar', 'fq=foo:Folder'])


def test_suite():
    return defaultTestLoader.loadTestsFromName(__name__)

if __name__ == '__main__':
    main(defaultTest='test_suite')
