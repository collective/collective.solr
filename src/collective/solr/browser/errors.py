# -*- coding: utf-8 -*-
from Products.Five import BrowserView
from zope.component.hooks import getSite


class ErrorView(BrowserView):

    def __init__(self, context, request):
        # since this is a view adapting an exception and a request (instead
        # of a regular content object and a request), the exception object
        # was passed as the context;  therefore we need to construct a
        # proper context in order to render the template in a sane manner;
        # normally we could use `getUtility(ISiteRoot)` for that, but then
        # `REQUEST` is missing, we'll employ the getSite hook ...
        self.exception = context
        self.context = getSite()
        self.request = request

    def errorInfo(self):
        """ provide error type and value """
        type_ = str(self.exception.__class__).replace(
            "<class '", '').replace("'>", '')
        return {
            'type': type_,
            'value': self.exception.args,
        }
