from os.path import dirname, join
from httplib import HTTPConnection
from threading import Thread
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from StringIO import StringIO
from socket import error
from sys import stderr
from re import search

from collective.solr.local import getLocal, setLocal
from collective.solr import tests


def getData(filename):
    """ return a file object from the test data folder """
    filename = join(dirname(tests.__file__), 'data', filename)
    return open(filename, 'r').read()


def fakehttp(solrconn, *fakedata):
    """ helper function to set up a fake http request on a SolrConnection """

    class FakeOutput(list):
        """ helper class to organize output from fake connections """

        conn = solrconn

        def log(self, item):
            self.current.append(item)

        def get(self, skip=0):
            self[:] = self[skip:]
            return ''.join(self.pop(0)).replace('\r', '')

        def new(self):
            self.current = []
            self.append(self.current)

        def __len__(self):
            self.conn.flush()   # send out all pending xml
            return super(FakeOutput, self).__len__()

        def __str__(self):
            self.conn.flush()   # send out all pending xml
            if self:
                return ''.join(self[0]).replace('\r', '')
            else:
                return ''

    output = FakeOutput()

    class FakeSocket(StringIO):
        """ helper class to fake socket communication """

        def sendall(self, str):
            output.log(str)

        def makefile(self, mode, name):
            return self

        def read(self, amt=None):
            if self.closed:
                return ''
            return StringIO.read(self, amt)

        def readline(self, length=None):
            if self.closed:
                return ''
            return StringIO.readline(self, length)

    class FakeHTTPConnection(HTTPConnection):
        """ helper class to fake a http connection object from httplib.py """

        def __init__(self, host, *fakedata):
            HTTPConnection.__init__(self, host)
            self.fakedata = list(fakedata)

        def putrequest(self, *args, **kw):
            response = self.fakedata.pop(0)     # get first response
            self.sock = FakeSocket(response)    # and set up a fake socket
            output.new()                        # as well as an output buffer
            HTTPConnection.putrequest(self, *args, **kw)

        def setTimeout(self, timeout):
            pass

    solrconn.conn = FakeHTTPConnection(solrconn.conn.host, *fakedata)
    return output


def fakemore(solrconn, *fakedata):
    """ helper function to add more fake http requests to a SolrConnection """
    assert hasattr(solrconn.conn, 'fakedata')   # `isinstance()` doesn't work?
    solrconn.conn.fakedata.extend(fakedata)


def fakeServer(actions, port=55555):
    """ helper to set up and activate a fake http server used for testing
        purposes; <actions> must be a list of handler functions, which will
        receive the base handler as their only argument and are used to
        process the incoming requests in turn; returns a thread that should
        be 'joined' when done """
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            action = actions.pop(0)             # get next action
            action(self)                        # and process it...
        def do_GET(self):
            action = actions.pop(0)             # get next action
            action(self)                        # and process it...
        def log_request(*args, **kw):
            pass
    def runner():
        while actions:
            server.handle_request()
    server = HTTPServer(('', port), Handler)
    thread = Thread(target=runner)
    thread.start()
    return thread


def pingSolr():
    """ test if the solr server is available """
    status = getLocal('solrStatus')
    if status is not None:
        return status
    conn = HTTPConnection('localhost', 8983)
    try:
        conn.request('GET', '/solr/admin/ping')
        response = conn.getresponse()
        status = response.status == 200
        msg = "INFO: solr return status '%s'" % response.status
    except error, e:
        status = False
        msg = 'WARNING: solr tests could not be run: "%s".' % e
    if not status:
        print >> stderr
        print >> stderr, '*' * len(msg)
        print >> stderr, msg
        print >> stderr, '*' * len(msg)
        print >> stderr
    setLocal('solrStatus', status)
    return status


def numFound(result):
    match = search(r'numFound="(\d+)"', result)
    if match is not None:
        match = int(match.group(1))
    return match
