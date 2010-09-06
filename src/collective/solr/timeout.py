import sys
from urllib2 import build_opener, HTTPHandler
from httplib import HTTPConnection
from socket import getaddrinfo, socket, error, SOCK_STREAM

PYTHON26 = sys.version_info >= (2, 6)


class HTTPConnectionWithTimeout(HTTPConnection):

    if not PYTHON26:
        # In Python 2.6, the HTTPConnection has timeout handling itself

        def __init__(self, host, port=None, strict=None, timeout=None):
            HTTPConnection.__init__(self, host, port, strict)
            self.timeout = timeout

        def connect(self):
            """ copied from httplib.py and added timeout handling """
            msg = "getaddrinfo returns an empty list"
            for res in getaddrinfo(self.host, self.port, 0, SOCK_STREAM):
                af, socktype, proto, canonname, sa = res
                try:
                    self.sock = socket(af, socktype, proto)
                    # set the timeout if given...
                    if self.timeout is not None:
                        self.sock.settimeout(self.timeout)
                    if self.debuglevel > 0:
                        print "connect: (%s, %s)" % (self.host, self.port)
                    self.sock.connect(sa)
                except error, msg:
                    if self.debuglevel > 0:
                        print 'connect fail:', (self.host, self.port)
                    if self.sock:
                        self.sock.close()
                    self.sock = None
                    continue
                break
            if not self.sock:
                raise error(msg)

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
