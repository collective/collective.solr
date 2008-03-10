from unittest import TestCase, TestSuite, makeSuite, main
from collective.solr.solr import SolrConnection
from collective.solr.tests.utils import getData, fakehttp


class TestSolr(TestCase):

    def test_add(self):
        add_request = getData('add_request.txt')
        add_response = getData('add_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, add_response)
        res = c.add(id='500',name='python test doc')

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

    def test_commit(self):
        commit_request = getData('commit_request.txt')
        commit_response = getData('commit_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        res = c.commit()

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
        res = c.commit(optimize=True)

        self.failUnlessEqual(str(output), commit_request)

    def test_commit_no_wait_flush(self):
        commit_request = getData('commit_request.txt')
        commit_response = getData('commit_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        res = c.commit(waitFlush=False)

        self.failUnlessEqual(str(output), commit_request)

    def test_commit_no_wait_searcher(self):
        commit_request = getData('commit_request_no_wait_searcher.txt')
        commit_response = getData('commit_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        res = c.commit(waitSearcher=False)

        self.failUnlessEqual(str(output), commit_request)

    def test_commit_no_wait(self):
        commit_request = getData('commit_request_no_wait.txt')
        commit_response = getData('commit_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, commit_response)
        res = c.commit(waitFlush=False, waitSearcher=False)

        self.failUnlessEqual(str(output), commit_request)

    def test_search(self):
        search_request = getData('search_request.txt')
        search_response = getData('search_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, search_response)
        res = c.search(q='id:[* TO *]', wt='xml', rows='10',indent='on')

        self.failUnlessEqual(str(output), search_request)

        self.failUnless(res.find(('.//doc')))

    def test_delete(self):
        delete_request = getData('delete_request.txt')
        delete_response = getData('delete_response.txt')

        c = SolrConnection(host='localhost:8983', persistent=True)
        output = fakehttp(c, delete_response)
        res = c.delete('500')

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


def test_suite():
    return TestSuite((
        makeSuite(TestSolr),
    ))

if __name__ == '__main__':
    main(defaultTest='test_suite')

