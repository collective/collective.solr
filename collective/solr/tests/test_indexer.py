from unittest import TestCase, TestSuite, makeSuite, main
from DateTime import DateTime

from collective.solr.indexer import SolrIndexQueueProcessor
from collective.solr.tests.test_solr import fakehttp
from collective.solr.tests.utils import getData


class Foo:
    """ dummy test object """
    def __init__(self, **kw):
        for key, value in kw.items():
            setattr(self, key, value)


class QueueIndexerTests(TestCase):

    def testPrepareData(self):
        data = {'allowedRolesAndUsers': ['user:test_user_1_', 'user:portal_owner']}
        SolrIndexQueueProcessor().prepareData(data)
        self.assertEqual(data, {'allowedRolesAndUsers': ['user$test_user_1_', 'user$portal_owner']})

    def setupProcessor(self):
        proc = SolrIndexQueueProcessor()
        proc.setHost()
        conn = proc.getConnection()
        fakehttp(conn, getData('schema.xml'), [])   # fake schema response
        proc.getSchema()                            # read and cache the schema
        return proc

    def testIndexObject(self):
        proc = self.setupProcessor()
        output = []
        response = getData('add_response.txt')
        fakehttp(proc.getConnection(), response, output)    # fake add response
        proc.index(Foo(id='500', name='python test doc'))   # indexing sends data
        output = ''.join(output).replace('\r', '')
        self.assertEqual(output, getData('add_request.txt'))

    def testPartialIndexObject(self):
        proc = self.setupProcessor()
        foo = Foo(id='500', name='foo', price=42.0)
        # first index all attributes...
        output = []
        response = getData('add_response.txt')
        fakehttp(proc.getConnection(), response, output)
        proc.index(foo)
        output = ''.join(output).replace('\r', '')
        self.assert_(output.find('<field name="price">42.0</field>') > 0, '"price" data not found')
        # then only a subset...
        output = []
        response = getData('add_response.txt')
        fakehttp(proc.getConnection(), response, output)
        proc.index(foo, attributes=['id', 'name'])
        output = ''.join(output).replace('\r', '')
        self.assert_(output.find('<field name="name">foo</field>') > 0, '"name" data not found')
        self.assertEqual(output.find('price'), -1, '"price" data found?')
        self.assertEqual(output.find('42'), -1, '"price" data found?')

    def testDateIndexing(self):
        proc = self.setupProcessor()
        foo = Foo(id='zeidler', name='andi', cat='nerd', timestamp=DateTime('May 11 1972 03:45 GMT'))
        output = []
        response = getData('add_response.txt')
        fakehttp(proc.getConnection(), response, output)    # fake add response
        proc.index(foo)
        output = ''.join(output).replace('\r', '')
        required = '<field name="timestamp">1972-05-11T03:45:00.000Z</field>'
        self.assert_(output.find(required) > 0, '"date" data not found')

    def testReindexObject(self):
        proc = self.setupProcessor()
        output = []
        response = getData('add_response.txt')
        fakehttp(proc.getConnection(), response, output)    # fake add response
        proc.reindex(Foo(id='500', name='python test doc')) # reindexing sends data
        output = ''.join(output).replace('\r', '')
        self.assertEqual(output, getData('add_request.txt'))

    def testUnindexObject(self):
        proc = self.setupProcessor()
        output = []
        response = getData('delete_response.txt')
        fakehttp(proc.getConnection(), response, output)    # fake response
        proc.unindex(Foo(id='500', name='python test doc')) # unindexing sends data
        output = ''.join(output).replace('\r', '')
        self.assertEqual(output, getData('delete_request.txt'))

    def testCommit(self):
        proc = self.setupProcessor()
        output = []
        response = getData('commit_response.txt')
        fakehttp(proc.getConnection(), response, output)    # fake response
        proc.commit()                                       # committing sends data
        output = ''.join(output).replace('\r', '')
        self.assertEqual(output, getData('commit_request.txt'))


def test_suite():
    return TestSuite([
        makeSuite(QueueIndexerTests),
    ])

if __name__ == '__main__':
    main(defaultTest='test_suite')

