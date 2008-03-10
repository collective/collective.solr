from os.path import dirname, join
from httplib import HTTPConnection
from StringIO import StringIO
from collective.solr import tests


def getData(filename):
    """Return file as string"""
    filename = join(dirname(tests.__file__), 'data', filename)
    return open(filename, 'r').read()


def fakehttp(solrconn, fakedata):
    """ helper function to set up a fake http request on a SolrConnection """

    class FakeOutput(list):
        """ helper class to organize output from fake connections """

        def __str__(self):
            return ''.join(self).replace('\r', '')

    output = FakeOutput()

    class FakeSocket(StringIO):
        """ helper class to fake socket communication """

        def sendall(self, str):
            output.append(str)

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

        def connect(self):
            self.sock = FakeSocket(fakedata)

    solrconn.conn = FakeHTTPConnection(solrconn.conn.host)
    return output

