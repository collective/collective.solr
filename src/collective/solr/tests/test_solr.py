from unittest import TestCase
from elementtree.ElementTree import fromstring
from collective.solr.solr import SolrConnection
from collective.solr.tests.utils import getData, fakehttp


class TestSolr(TestCase):

    def test_add(self):
        add_request = getData('add_request.txt')
        add_response = getData('add_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, add_response)
        c.add(id='500', name='python test doc')
        res = c.flush()
        self.assertEqual(len(res), 1)   # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), add_request)
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib['name'], 'status')
        self.failUnlessEqual(node.text, '0')
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib['name'], 'QTime')
        self.failUnlessEqual(node.text, '4')
        res.find('QTime')

    def test_add_with_boost_values(self):
        add_request = getData('add_request_with_boost_values.txt')
        add_response = getData('add_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, add_response)
        boost = {'': 2, 'id': 0.5, 'name': 5}
        c.add(boost_values=boost, id='500', name='python test doc')
        res = c.flush()
        self.assertEqual(len(res), 1)   # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), add_request)

    def test_commit(self):
        commit_request = getData('commit_request.txt')
        commit_response = getData('commit_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        res = c.commit()
        self.assertEqual(len(res), 1)   # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), commit_request)
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib['name'], 'status')
        self.failUnlessEqual(node.text, '0')
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib['name'], 'QTime')
        self.failUnlessEqual(node.text, '55')
        res.find('QTime')

    def test_optimize(self):
        commit_request = getData('optimize_request.txt')
        commit_response = getData('commit_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        c.commit(optimize=True)
        self.failUnlessEqual(str(output), commit_request)

    def test_commit_no_wait_flush(self):
        commit_request = getData('commit_request.txt')
        commit_response = getData('commit_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        c.commit(waitFlush=False)
        self.failUnlessEqual(str(output), commit_request)

    def test_commit_no_wait_searcher(self):
        commit_request = getData('commit_request_no_wait_searcher.txt')
        commit_response = getData('commit_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        c.commit(waitSearcher=False)
        self.failUnlessEqual(str(output), commit_request)

    def test_commit_no_wait(self):
        commit_request = getData('commit_request_no_wait.txt')
        commit_response = getData('commit_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        c.commit(waitFlush=False, waitSearcher=False)
        self.failUnlessEqual(str(output), commit_request)

    def test_search(self):
        search_request = getData('search_request.txt')
        search_response = getData('search_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, search_response)
        res = c.search(q='+id:[* TO *]', wt='xml', rows='10', indent='on')
        res = fromstring(res.read())
        self.failUnlessEqual(str(output), search_request)
        self.failUnless(res.find(('.//doc')))

    def test_delete(self):
        delete_request = getData('delete_request.txt')
        delete_response = getData('delete_response.txt')
        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, delete_response)
        c.delete('500')
        res = c.flush()
        self.assertEqual(len(res), 1)   # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), delete_request)
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib['name'], 'status')
        self.failUnlessEqual(node.text, '0')
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib['name'], 'QTime')
        self.failUnlessEqual(node.text, '0')
        res.find('QTime')
