from os.path import dirname, join
from httplib import HTTPConnection
from StringIO import StringIO
from collective.solr import tests


def getData(filename):
    """Return file as string"""
    filename = join(dirname(tests.__file__), 'data', filename)
    return open(filename, 'r').read()


def fakehttp(solrconn, *fakedata):
    """ helper function to set up a fake http request on a SolrConnection """

    class FakeOutput(list):
        """ helper class to organize output from fake connections """

        def log(self, item):
            self.current.append(item)

        def get(self, skip=0):
            self[:] = self[skip:]
            return ''.join(self.pop(0)).replace('\r', '')

        def new(self):
            self.current = []
            self.append(self.current)

        def __str__(self):
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
            output.new()                        # and create a new output buffer
            HTTPConnection.putrequest(self, *args, **kw)

    solrconn.conn = FakeHTTPConnection(solrconn.conn.host, *fakedata)
    return output

