__author__ = 'tamm'

from Products.Five import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile


class SearchTypeahead(BrowserView):

    batching_template = ViewPageTemplateFile('typeahead_batching.pt')
    iscroll_template = ViewPageTemplateFile('typeahead_iscroll.pt')

    BATCHING = False

    def __call__(self, *args, **kwargs):
        if self.BATCHING:
            return self.batching_template()
        return self.iscroll_template()
