__author__ = 'tamm'

from collective.solr.interfaces import ITypeaheadSearchConfig

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile

from zope.component import queryUtility


class SearchTypeahead(BrowserView):

    batching_template = ViewPageTemplateFile('typeahead_batching.pt')
    iscroll_template = ViewPageTemplateFile('typeahead_iscroll.pt')

    BATCHING = False

    def __call__(self, *args, **kwargs):
        self.config = queryUtility(ITypeaheadSearchConfig)

        if self.config.results_page_mode == u'Batching':
            return self.batching_template()

        if self.config.results_page_mode == u'InfiniteScroll':
            return self.iscroll_template()
