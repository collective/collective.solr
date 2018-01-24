# -*- coding: utf-8 -*-
from unittest import TestCase
from urllib import unquote

from zope.component import provideUtility
from zope.publisher.browser import TestRequest
from zope.schema.vocabulary import SimpleTerm

from collective.solr.browser.facets import convertFacets, facetParameters
from collective.solr.browser.facets import SearchFacetsView
from collective.solr.interfaces import IFacetTitleVocabularyFactory
from collective.solr.parser import SolrResponse
from collective.solr.testing import COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE
from collective.solr.tests.utils import getData
from collective.solr.utils import getConfig
from collective.solr.vocabularies import I18NFacetTitlesVocabularyFactory


class Dummy(object):

    """ dummy class that allows setting attributes """

    def __init__(self, **kw):
        self.__dict__.update(kw)


class DummyView(object):

    def __init__(self, context=None, request=None):
        if context is not None:
            self.context = context
        else:
            self.context = Dummy()
        if request is not None:
            self.request = request
        else:
            self.request = {}


class DummyTitleVocabulary(object):

    def __contains__(self, term):
        return True

    def getTerm(self, term):
        return SimpleTerm(term, title='Title of %s' % term.capitalize())


class DummyTitleVocabularyFactory(object):

    def __call__(self, context):
        return DummyTitleVocabulary()


class DummyAllCapsVocabulary(object):

    def __contains__(self, term):
        return term != 'leavelowercase'

    def getTerm(self, term):
        return SimpleTerm(term, title=term.upper())


class DummyAllCapsVocabularyFactory(object):

    def __call__(self, context):
        return DummyAllCapsVocabulary()


class FacettingHelperTest(TestCase):

    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def setUp(self):
        provideUtility(
            DummyTitleVocabularyFactory(),
            IFacetTitleVocabularyFactory
        )
        provideUtility(
            DummyAllCapsVocabularyFactory(), IFacetTitleVocabularyFactory,
            name='capsFacet')

    def test_i18n_facet_titles(self):
        voc = I18NFacetTitlesVocabularyFactory()(context=None)
        self.assertTrue('Bogus' in voc)
        term = voc.getTerm(u'München')
        # self.assertEqual(term.token, 'Mnchen')  XXX different on 4.3 and 5.x
        self.assertEqual(term.value, u'München')
        self.assertEqual(term.title, u'München')

    def testConvertFacets(self):
        fields = dict(portal_type=dict(Document=10,
                                       Folder=3, Event=5, Topic=2))
        view = DummyView(context=Dummy(), request=TestRequest())
        info = convertFacets(fields, view=view)
        # the info should consist of 1 dict with
        # `counts`, `name` and `title` keys
        self.assertEqual([sorted(i) for i in info],
                         [['counts', 'name', 'title']] * 1)
        # next let's check the field names
        self.assertEqual([i['title'] for i in info], ['portal_type'])
        # and the fields contents
        types, = info
        self.assertEqual(types['title'], 'portal_type')
        self.assertEqual(
            [(c['name'], c['title'], c['count']) for c in types['counts']],
            [('Document', 'Title of Document', 10),
             ('Event', 'Title of Event', 5),
             ('Folder', 'Title of Folder', 3),
             ('Topic', 'Title of Topic', 2)])

    def testConvertFacetResponse(self):
        response = SolrResponse(getData('facet_xml_response.txt'))
        fields = response.facet_counts['facet_fields']
        view = DummyView(request=TestRequest())
        info = convertFacets(fields, view=view)
        # the info should consist of 2 dicts with
        # `counts`, `name` and `title` keys
        self.assertEqual([sorted(i)
                          for i in info], [['counts', 'name', 'title']] * 2)
        # next let's check the field names
        self.assertEqual([i['title'] for i in info], ['cat', 'inStock'])
        # and the fields contents
        cat, inStock = info
        self.assertEqual(cat['title'], 'cat')
        self.assertEqual(
            [(c['name'], c['title'], c['count']) for c in cat['counts']],
            [('search', 'Title of Search', 1),
             ('software', 'Title of Software', 1),
             ('electronics', 'Title of Electronics', 0),
             ('monitor', 'Title of Monitor', 0)])
        self.assertEqual(inStock['title'], 'inStock')
        self.assertEqual(
            [(c['name'], c['count']) for c in inStock['counts']],
            [('true', 1)])

    def testFacetParameters(self):
        context = Dummy()
        request = {}
        view = DummyView(context, request)
        # with nothing set up, no facets will be returned
        self.assertEqual(facetParameters(view), ([], {}))
        # setting up the regular config utility should give the default value
        cfg = getConfig()
        self.assertEqual(facetParameters(view), ([], {}))
        # so let's set it...
        cfg.facets = ['foo']
        self.assertEqual(facetParameters(view), (['foo'], {}))
        # override the setting on the context
        context.facet_fields = ['bar']
        self.assertEqual(facetParameters(view), (['bar'], {}))
        # and again via the request
        request['facet.field'] = ['foo', 'bar']
        self.assertEqual(facetParameters(view),
                         (['foo', 'bar'], {}))

    def testFacetDependencies(self):
        cfg = getConfig()
        # dependency info can be set via the configuration utility...
        cfg.facets = ['foo:bar']
        context = Dummy()
        request = {}
        view = DummyView(context, request)
        self.assertEqual(facetParameters(view),
                         (['foo:bar'], dict(foo=['bar'])))
        # overridden on the context
        context.facet_fields = ['bar:foo']
        self.assertEqual(facetParameters(view),
                         (['bar:foo'], dict(bar=['foo'])))
        # and via the request
        request['facet.field'] = ['foo:bar', 'bar:foo']
        self.assertEqual(
            facetParameters(view),
            (['foo:bar', 'bar:foo'], dict(foo=['bar'], bar=['foo']))
        )
        # white space shouldn't matter
        request['facet.field'] = ['foo : bar', 'bar  :foo']
        self.assertEqual(
            facetParameters(view),
            (['foo : bar', 'bar  :foo'], dict(foo=['bar'], bar=['foo']))
        )

        # XXX: Manually clean up after the test. We should be able to remove
        # this once our test isolation issues have been dealt with.
        cfg.facets = []

    def testNamedFacetTitleVocabulary(self):
        """Test use of IFacetTitleVocabularyFactory registrations

        If a IFacetTitleVocabularyFactory is registered under the same name
        as the facet field, use that to look up titles

        """
        context = Dummy(facet_fields=['capsFacet'])
        request = TestRequest(form=dict(foo='bar'))
        fields = dict(capsFacet=dict(one=10, two=3, leavelowercase=5))
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        self.assertEqual(len(info), 1)
        counts = info[0]['counts']
        self.assertEqual(len(counts), 3)
        self.assertEqual(counts[0]['title'], 'ONE')
        self.assertEqual(counts[1]['title'], 'leavelowercase')
        self.assertEqual(counts[2]['title'], 'TWO')

    def testFacetLinks(self):
        context = Dummy(facet_fields=['portal_type'])
        request = TestRequest(form=dict(foo='bar'))
        fields = dict(portal_type=dict(Document=10, Folder=3, Event=5))
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        # let's check queries for the one and only facet field
        self.assertEqual(len(info), 1)
        counts = info[0]['counts']
        self.assertEqual(len(counts), 3)
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(counts[0]['name'], 'Document')
        self.assertEqual(params(counts[0]['query']), [
            'foo=bar', 'fq=portal_type:"Document"'])
        self.assertEqual(counts[1]['name'], 'Event')
        self.assertEqual(params(counts[1]['query']), [
            'foo=bar', 'fq=portal_type:"Event"'])
        self.assertEqual(counts[2]['name'], 'Folder')
        self.assertEqual(params(counts[2]['query']), [
            'foo=bar', 'fq=portal_type:"Folder"'])

    def testFacetLinksWithSelectedFacet(self):
        context = Dummy()
        request = TestRequest(form={'foo': 'bar', 'facet.field': 'bar'})
        fields = dict(foo=dict(private=2, published=4))
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        self.assertEqual(len(info), 1)
        counts = info[0]['counts']
        self.assertEqual(len(counts), 2)
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(counts[0]['name'], 'published')
        self.assertEqual(params(counts[0]['query']), [
            'facet.field=bar', 'foo=bar', 'fq=foo:"published"'])
        self.assertEqual(counts[1]['name'], 'private')
        self.assertEqual(params(counts[1]['query']), [
            'facet.field=bar', 'foo=bar', 'fq=foo:"private"'])

    def testFacetLinksWithMultipleFacets(self):
        context = Dummy()
        request = TestRequest(form={'facet.field': ['foo', 'bar']})
        fields = dict(foo=dict(Document=10, Folder=3, Event=5),
                      bar=dict(private=2, published=4))
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        self.assertEqual(len(info), 2)
        # check the facets for 'bar'
        bars = info[1]['counts']
        self.assertEqual(len(bars), 2)
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(params(bars[0]['query']), [
            'facet.field=foo', 'fq=bar:"published"'])
        self.assertEqual(params(bars[1]['query']), [
            'facet.field=foo', 'fq=bar:"private"'])
        # and also the one for 'foo'
        foos = info[0]['counts']
        self.assertEqual(len(foos), 3)
        self.assertEqual(params(foos[0]['query']), [
            'facet.field=bar', 'fq=foo:"Document"'])
        self.assertEqual(params(foos[1]['query']), [
            'facet.field=bar', 'fq=foo:"Event"'])
        self.assertEqual(params(foos[2]['query']), [
            'facet.field=bar', 'fq=foo:"Folder"'])

    def testFacetLinksWithMultipleSelectedFacets(self):
        context = Dummy()
        request = TestRequest(form={'facet.field': 'foo', 'fq': 'bar:private'})
        fields = dict(foo=dict(Document=3, Folder=2))
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        self.assertEqual(len(info), 1)
        counts = info[0]['counts']
        params = lambda query: sorted(map(unquote, query.split('&')))
        self.assertEqual(params(counts[0]['query']), [
            'fq=bar:private', 'fq=foo:"Document"'])
        self.assertEqual(params(counts[1]['query']), [
            'fq=bar:private', 'fq=foo:"Folder"'])

    def testSelectedFacetsInformation(self):
        request = TestRequest()
        selected = SearchFacetsView(Dummy(), request).selected
        # initially no facets are seleted
        self.assertEqual(selected(), [])
        # so let's select one...
        params = lambda query: sorted(map(unquote, query.split('&')))
        info = lambda: [(i['title'], params(i['query'])) for i in selected()]
        request.form['fq'] = 'foo:"xy"'
        self.assertEqual(info(), [
            ('foo', ['facet.field=foo']),
        ])
        # and then some more...
        request.form['fq'] = ['foo:"x"', 'bar:"y"']
        self.assertEqual(info(), [
            ('foo', ['facet.field=foo', 'fq=bar:"y"']),
            ('bar', ['facet.field=bar', 'fq=foo:"x"']),
        ])
        request.form['fq'] = ['foo:"x"', 'bar:"y"', 'bah:"z"']
        self.assertEqual(info(), [
            ('foo', ['facet.field=foo', 'fq=bah:"z"', 'fq=bar:"y"']),
            ('bar', ['facet.field=bar', 'fq=bah:"z"', 'fq=foo:"x"']),
            ('bah', ['facet.field=bah', 'fq=bar:"y"', 'fq=foo:"x"']),
        ])
        # extra parameter should be left untouched
        request.form['foo'] = 'bar'
        self.assertEqual(info(), [
            ('foo', [
             'facet.field=foo', 'foo=bar', 'fq=bah:"z"', 'fq=bar:"y"']),
            ('bar', [
             'facet.field=bar', 'foo=bar', 'fq=bah:"z"', 'fq=foo:"x"']),
            ('bah', [
             'facet.field=bah', 'foo=bar', 'fq=bar:"y"', 'fq=foo:"x"']),
        ])
        # an existing 'facet.field' parameter should be preserved
        del request.form['foo']
        request.form['facet.field'] = 'x'
        self.assertEqual(info(), [
            ('foo', [
             'facet.field=foo', 'facet.field=x', 'fq=bah:"z"', 'fq=bar:"y"']),
            ('bar', [
             'facet.field=bar', 'facet.field=x', 'fq=bah:"z"', 'fq=foo:"x"']),
            ('bah', [
             'facet.field=bah', 'facet.field=x', 'fq=bar:"y"', 'fq=foo:"x"']),
        ])

    def testSelectedFacetValues(self):
        request = TestRequest()
        selected = SearchFacetsView(Dummy(), request).selected
        info = lambda: [(i['title'], i['value']) for i in selected()]
        request.form['fq'] = 'foo:"xy"'
        self.assertEqual(info(), [('foo', 'Title of Xy')])
        request.form['fq'] = ['foo:"x"', 'bar:"y"']
        self.assertEqual(info(),
                         [('foo', 'Title of X'), ('bar', 'Title of Y')])
        request.form['fq'] = ['foo:"x"', 'bar:"y"', 'bah:"z"']
        self.assertEqual(info(), [('foo', 'Title of X'), ('bar', 'Title of Y'),
                                  ('bah', 'Title of Z')])

    def testEmptyFacetField(self):
        context = Dummy()
        request = TestRequest(form={'facet.field': 'Subject'})
        fields = dict(Subject=dict())
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        self.assertEqual(info, [])

    def testEmptyFacetFieldWithZeroCounts(self):
        fields = dict(foo={'foo': 0, 'bar': 0})
        results = Dummy(facet_counts=dict(facet_fields=fields))
        view = SearchFacetsView(Dummy(), TestRequest())
        view.kw = dict(results=results)
        self.assertEqual(view.facets(), [])

    def testFacetFieldFilter(self):
        context = Dummy()
        request = TestRequest(form={'facet.field': 'foo'})
        fields = dict(foo={'foo': 2, 'bar': 4, '': 6, 'nil': 0})
        # without a filter all values are included
        view = DummyView(context=context, request=request)
        info = convertFacets(fields, view)
        self.assertEqual(len(info), 1)
        self.assertEqual(
            [(c['name'], c['count']) for c in info[0]['counts']],
            [
                ('', 6),
                ('bar', 4),
                ('foo', 2),
                ('nil', 0),
            ]
        )
        # let's filter out zero counts
        filter = lambda name, count: count > 0
        info = convertFacets(fields, view, filter=filter)
        self.assertEqual(len(info), 1)
        self.assertEqual(
            [(c['name'], c['count']) for c in info[0]['counts']],
            [
                ('', 6),
                ('bar', 4),
                ('foo', 2),
            ]
        )
        # and also unnamed facets
        filter = lambda name, count: name and count > 0
        info = convertFacets(fields, view, filter=filter)
        self.assertEqual(len(info), 1)
        self.assertEqual(
            [(c['name'], c['count']) for c in info[0]['counts']],
            [
                ('bar', 4),
                ('foo', 2),
            ]
        )
