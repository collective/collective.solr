from Products.Five import BrowserView


class ErrorView(BrowserView):

    def __init__(self, context, request):
        # since this is a view adapting an exception and a request (instead
        # of a regular content object and a request), the exception object
        # was passed as the context;  therefore we need to construct a
        # proper context in order to render the template in a sane manner;
        # normally we could use `getUtility(ISiteRoot)` for that, but then
        # `REQUEST` is missing, we'll employ the portal state view...
        self.exception = context
        self.context = request.traverse('@@plone_portal_state').portal()
        self.request = request

    def errorInfo(self):
        """ provide error type and value """
        # In Python < 2.6 the string representation of an exception was:
        # "socket.error". In Python 2.6+ it's: "<class 'socket.error'>"
        type_ = str(self.exception.__class__)
        if '<class' in type_:
            type_ = type_.replace("<class '", "").replace("'>", '')
        return {
            'type': type_,
            'value': self.exception.args,
        }
