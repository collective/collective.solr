from unittest import TestCase
from xml.etree.cElementTree import fromstring

from collective.solr.solr import SolrConnection
from collective.solr.testing import COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE
from collective.solr.tests.utils import fakehttp, getData
from collective.solr.utils import getConfig


class TestSolr(TestCase):

    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def test_add(self):
        config = getConfig()
        config.atomic_updates = True
        add_request = getData("add_request.txt").rstrip(b"\n")
        add_response = getData("add_response.txt")

        c = SolrConnection(host="localhost:8983", persistent=True)

        # fake schema response - caches the schema
        fakehttp(c, getData("schema.xml"))
        c.get_schema()

        output = fakehttp(c, add_response)
        c.add(id="500", name="python test doc")
        res = c.flush()
        self.assertEqual(len(res), 1)  # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), add_request.decode("utf-8"))
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib["name"], "status")
        self.failUnlessEqual(node.text, "0")
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib["name"], "QTime")
        self.failUnlessEqual(node.text, "4")
        res.find("QTime")

    def test_add_with_boost_values(self):
        config = getConfig()
        config.atomic_updates = False
        add_request = getData("add_request_with_boost_values.txt").rstrip(b"\n")
        add_response = getData("add_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)

        # fake schema response - caches the schema
        fakehttp(c, getData("schema.xml"))
        c.get_schema()

        output = fakehttp(c, add_response)
        boost = {"": 2, "id": 0.5, "name": 5}
        c.add(
            boost_values=boost,
            atomic_updates=False,  # Force disabling atomic updates
            id="500",
            name="python test doc",
        )

        res = c.flush()
        self.assertEqual(len(res), 1)  # one request was sent
        self.failUnlessEqual(str(output), add_request.decode("utf-8"))

    def test_connection_str(self):
        c = SolrConnection(host="localhost:8983", persistent=True)
        self.assertEqual(
            str(c),
            "SolrConnection{host=localhost:8983, solrBase=/solr/plone, "
            "persistent=True, postHeaders={'Content-Type': 'text/xml; "
            "charset=utf-8'}, reconnects=0, login=None, password=None}",
        )

    def test_connection_str_authentication(self):
        c = SolrConnection(
            host="localhost:8983", persistent=True, login="login", password="password"
        )
        self.assertEqual(
            str(c),
            "SolrConnection{host=localhost:8983, solrBase=/solr/plone, "
            "persistent=True, postHeaders={'Content-Type': 'text/xml; "
            "charset=utf-8', 'Authorization': 'Basic ***'}, "
            "reconnects=0, login=login, password=***}",
        )

    def test_commit(self):
        commit_request = getData("commit_request.txt").rstrip(b"\n")
        commit_response = getData("commit_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        output = fakehttp(c, commit_response)
        res = c.commit()
        self.assertEqual(len(res), 1)  # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), commit_request.decode("utf-8"))
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib["name"], "status")
        self.failUnlessEqual(node.text, "0")
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib["name"], "QTime")
        self.failUnlessEqual(node.text, "55")
        res.find("QTime")

    def test_commit_with_authentication(self):
        commit_request = getData("commit_request_authentication.txt").rstrip(b"\n")
        commit_response = getData("commit_response.txt")
        c = SolrConnection(
            host="localhost:8983", persistent=True, login="login", password="password"
        )
        output = fakehttp(c, commit_response)
        res = c.commit()
        self.assertEqual(len(res), 1)  # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), commit_request.decode("utf-8"))
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib["name"], "status")
        self.failUnlessEqual(node.text, "0")
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib["name"], "QTime")
        self.failUnlessEqual(node.text, "55")
        res.find("QTime")

    def test_optimize(self):
        commit_request = getData("optimize_request.txt").rstrip(b"\n")
        commit_response = getData("commit_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        output = fakehttp(c, commit_response)
        c.commit(optimize=True)
        self.failUnlessEqual(str(output), commit_request.decode("utf-8"))

    def test_commit_no_wait_flush(self):
        commit_request = getData("commit_request.txt").rstrip(b"\n")
        commit_response = getData("commit_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        output = fakehttp(c, commit_response)
        c.commit()
        self.failUnlessEqual(str(output), commit_request.decode("utf-8"))

    def test_commit_no_wait_searcher(self):
        commit_request = getData("commit_request_no_wait_searcher.txt").rstrip(b"\n")
        commit_response = getData("commit_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        output = fakehttp(c, commit_response)
        c.commit(waitSearcher=False)
        self.failUnlessEqual(str(output), commit_request.decode("utf-8"))

    def test_search(self):
        # XXX: Solr 7 has a new query param 'q.op' which can not be passed to
        # the search method in Python.
        # This is why we have commented out code here.
        search_request = getData("search_request.txt").rstrip(b"\n")
        search_request_py2 = getData("search_request_py2.txt").rstrip(b"\n")
        search_response = getData("search_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        output = fakehttp(c, search_response)
        parameters = {
            "q": "+id:[* TO *]",
            "fl": "* score",
            "wt": "xml",
            "rows": "10",
            "indent": "on",
            "q.op": "AND",
            "lowercaseOperators": "true",
            "sow": "true",
        }

        res = c.search(**parameters)
        res = fromstring(res.read())
        normalize = lambda x: sorted(x.split(b"&"))  # sort request params
        self.assertIn(
            normalize(output.get()),
            [normalize(search_request), normalize(search_request_py2)],
        )
        self.failUnless(res.find((".//doc")))

    def test_search_with_default_request_handler(self):
        search_response = getData("search_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        fakehttp(c, search_response)
        c.search(q="+id:[* TO *]")
        self.assertEqual("/solr/plone/select", c.conn.url)

    def test_search_with_custom_request_handler(self):
        search_response = getData("search_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        fakehttp(c, search_response)
        c.search(request_handler="custom", q="+id:[* TO *]")
        self.assertEqual("/solr/plone/custom", c.conn.url)

    def test_delete(self):
        delete_request = getData("delete_request.txt").rstrip(b"\n")
        delete_response = getData("delete_response.txt")
        c = SolrConnection(host="localhost:8983", persistent=True)
        output = fakehttp(c, delete_response)
        c.delete("500")
        res = c.flush()
        self.assertEqual(len(res), 1)  # one request was sent
        res = res[0]
        self.failUnlessEqual(str(output), delete_request.decode("utf-8"))
        # Status
        node = res.findall(".//int")[0]
        self.failUnlessEqual(node.attrib["name"], "status")
        self.failUnlessEqual(node.text, "0")
        # QTime
        node = res.findall(".//int")[1]
        self.failUnlessEqual(node.attrib["name"], "QTime")
        self.failUnlessEqual(node.text, "0")
        res.find("QTime")
