from __future__ import print_function

from os.path import dirname, join
from re import search
from socket import error
from sys import stderr
from threading import Thread

import six
from collective.solr import tests
from collective.solr.local import getLocal, setLocal
from six.moves.BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
from six.moves.http_client import HTTPConnection
from zope.component.hooks import getSite, setSite

try:
    from Zope2.App import zcml
except ImportError:
    from Products.Five import zcml


def loadZCMLString(string):
    # Unset current site for Zope 2.13
    saved = getSite()
    setSite(None)
    try:
        zcml.load_string(string)
    finally:
        setSite(saved)


def getData(filename):
    """return a file object from the test data folder"""
    filename = join(dirname(tests.__file__), "data", filename)
    return open(filename, "rb").read()


def fakehttp(solrconn, *fakedata):
    """helper function to set up a fake http request on a SolrConnection"""

    class FakeOutput(list):

        """helper class to organize output from fake connections"""

        conn = solrconn

        def log(self, item):
            self.current.append(item)

        def get(self, skip=0):
            self[:] = self[skip:]
            return b"".join(self.pop(0)).replace(b"\r", b"")

        def new(self):
            self.current = []
            self.append(self.current)

        def __len__(self):
            self.conn.flush()  # send out all pending xml
            return super(FakeOutput, self).__len__()

        def __str__(self):
            self.conn.flush()  # send out all pending xml
            if self:
                return "".join([chunk.decode("utf-8") for chunk in self[0]]).replace(
                    "\r", ""
                )
            else:
                return ""

    output = FakeOutput()

    class FakeSocket(six.BytesIO):

        """helper class to fake socket communication"""

        def sendall(self, str):
            output.log(str)

        if six.PY2:

            def makefile(self, mode, name):
                return self

        else:

            def makefile(self, mode):
                return self

        def read(self, amt=None):
            if self.closed:
                return b""
            return six.BytesIO.read(self, amt)

        def readline(self, length=None):
            if self.closed:
                return b""
            return six.BytesIO.readline(self, length)

    class FakeHTTPConnection(HTTPConnection):

        """helper class to fake a http connection object from httplib.py"""

        def __init__(self, host, *fakedata):
            HTTPConnection.__init__(self, host)
            self.fakedata = list(fakedata)

        def putrequest(self, *args, **kw):
            self.url = args[1]
            response = self.fakedata.pop(0)  # get first response
            self.sock = FakeSocket(response)  # and set up a fake socket
            output.new()  # as well as an output buffer
            HTTPConnection.putrequest(self, *args, **kw)

        def setTimeout(self, timeout):
            pass

    solrconn.conn = FakeHTTPConnection(solrconn.conn.host, *fakedata)
    return output


def fakemore(solrconn, *fakedata):
    """helper function to add more fake http requests to a SolrConnection"""
    assert hasattr(solrconn.conn, "fakedata")  # `isinstance()` doesn't work?
    solrconn.conn.fakedata.extend(fakedata)


def fakeServer(actions, port=55555):
    """helper to set up and activate a fake http server used for testing
    purposes; <actions> must be a list of handler functions, which will
    receive the base handler as their only argument and are used to
    process the incoming requests in turn; returns a thread that should
    be 'joined' when done"""

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            action = actions.pop(0)  # get next action
            action(self)  # and process it...

        def do_GET(self):
            action = actions.pop(0)  # get next action
            action(self)  # and process it...

        def log_request(*args, **kw):
            pass

    def runner():
        while actions:
            server.handle_request()

    server = HTTPServer(("", port), Handler)
    thread = Thread(target=runner)
    thread.start()
    return thread


def pingSolr():
    """test if the solr server is available"""
    status = getLocal("solrStatus")
    if status is not None:
        return status
    conn = HTTPConnection("localhost", 8983)
    try:
        conn.request("GET", "/solr/plone/admin/ping")
        response = conn.getresponse()
        status = response.status == 200
        msg = "INFO: solr return status '%s'" % response.status
    except error as e:
        status = False
        msg = 'WARNING: solr tests could not be run: "%s".' % e
    if not status:
        print(file=stderr)
        print("*" * len(msg), file=stderr)
        print(msg, file=stderr)
        print("*" * len(msg), file=stderr)
        print(file=stderr)
    setLocal("solrStatus", status)
    return status


def numFound(result):
    if isinstance(result, six.binary_type):
        result = result.decode("utf-8")
    match = search(r'numFound="(\d+)"', result)
    if match is not None:
        match = int(match.group(1))
    return match
