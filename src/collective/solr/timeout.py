from urllib2 import build_opener, HTTPHandler
from httplib import HTTPConnection


class HTTPConnectionWithTimeout(HTTPConnection):

    def setTimeout(self, timeout):
        """ set a timeout value for the currently open connection as well
            as for future ones """
        self.timeout = timeout
        if self.sock is not None:
            self.sock.settimeout(timeout)


class HTTPHandlerWithTimeout(HTTPHandler):
    """ an http handler supporting timeouts on the underlying socket """

    def __init__(self, timeout=None, *args, **kw):
        HTTPHandler.__init__(self, *args, **kw)
        self.timeout = timeout

    def http_open(self, req):
        return self.do_open(self, req)

    def __call__(self, host, port=None, strict=None):
        """ the `do_open` function normally expects a class as its first
            parameter, which is then called to instantiate the handler class;
            unfortunately this way we cannot pass in a timeout;  however,
            `do_open` should be fine if we pass in ourselves and have
            `__call__` return a new connection object with the timeout set """
        return HTTPConnectionWithTimeout(host, port, strict, self.timeout)


def http_opener(timeout=None):
    """ create an urllib2 openerdirector with a httphandler supporting
        timeouts;  urls opened with the returned opener will have the
        given timeout set on any connection opened with `open` """
    return build_opener(HTTPHandlerWithTimeout(timeout=timeout))
