from unittest import TestCase, TestSuite, makeSuite, main
from collective.solr.solr import SolrConnection
from collective.solr.tests.utils import getData, fakehttp


class TestSolr(TestCase):

    def test_add(self):
        add_request = getData('add_request.txt')
        add_response = getData('add_response.txt')
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, add_response, output)
        res = c.add(id='500',name='python test doc')

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, add_request)
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
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, commit_response, output)
        res = c.commit()

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, commit_request)

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
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, commit_response, output)
        res = c.commit(optimize=True)

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, commit_request)

    def test_commit_no_wait_flush(self):
        commit_request = getData('commit_request.txt')
        commit_response = getData('commit_response.txt')
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, commit_response, output)
        res = c.commit(waitFlush=False)

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, commit_request)

    def test_commit_no_wait_searcher(self):
        commit_request = getData('commit_request_no_wait_searcher.txt')
        commit_response = getData('commit_response.txt')
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, commit_response, output)
        res = c.commit(waitSearcher=False)

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, commit_request)

    def test_commit_no_wait(self):
        commit_request = getData('commit_request_no_wait.txt')
        commit_response = getData('commit_response.txt')
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, commit_response, output)
        res = c.commit(waitFlush=False, waitSearcher=False)

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, commit_request)

    def test_search(self):
        search_request = getData('search_request.txt')
        search_response = getData('search_response.txt')
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, search_response, output)
        res = c.search(q='id:[* TO *]', wt='xml', rows='10',indent='on')

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, search_request)

        self.failUnless(res.find(('.//doc')))

    def test_delete(self):
        delete_request = getData('delete_request.txt')
        delete_response = getData('delete_response.txt')
        output = []

        c = SolrConnection(host='localhost:8983', persistent=True)
        fakehttp(c, delete_response, output)
        res = c.delete('500')

        output = ''.join(output).replace('\r','')
        self.failUnlessEqual(output, delete_request)

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

