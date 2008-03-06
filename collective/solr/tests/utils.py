from os.path import dirname, join
from collective.solr import tests


def getData(filename):
    """Return file as string"""
    filename = join(dirname(tests.__file__), 'data', filename)
    return open(filename, 'r').read()

