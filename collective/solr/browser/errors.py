from Products.Five import BrowserView


class ErrorView(BrowserView):

    def __init__(self, context, request):
        # since this is a view adapting an exception and a request (instead
        # of a regular content object and a request), the exception object
        # was passed as the context;  therefore we need to construct a
        # proper context in order to render the template in a sane manner...
        self.exception = context
        self.context = request.traverse('@@plone_portal_state').portal()
        self.request = request

    def errorInfo(self):
        """ provide error type and value """
        return {
            'type': str(self.exception.__class__),
            'value': self.exception.args,
        }


