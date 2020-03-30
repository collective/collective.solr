from unittest import TestCase
from threading import Thread
from re import search, findall, DOTALL
from DateTime import DateTime
from datetime import datetime
from datetime import date
from zope.interface import implementer
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware

from collective.solr.interfaces import ICheckIndexable
from collective.solr.manager import SolrConnectionManager
from collective.solr.indexer import SolrIndexProcessor
from collective.solr.indexer import logger as logger_indexer
from collective.solr.tests.utils import getData, fakehttp, fakemore
from collective.solr.testing import COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE
from collective.solr.solr import SolrConnection
from collective.solr.utils import getConfig
from collective.solr.utils import prepareData


@implementer(ICheckIndexable)
class Foo(CMFCatalogAware):

    """ dummy test object """

    def __init__(self, **kw):
        for key, value in kw.items():
            setattr(self, key, value)

    def __call__(self):
        return True


def sortFields(output):
    """ helper to sort `<field>` tags in output for testing """
    pattern = br"^(.*<doc>)(<field .*</field>)(</doc>.*)"
    prefix, fields, suffix = search(pattern, output, DOTALL).groups()
    tags = br"(<field [^>]*>[^<]*</field>)"
    return prefix + b"".join(sorted(findall(tags, fields))) + suffix


class QueueIndexerTests(TestCase):

    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def setUp(self):
        self.mngr = SolrConnectionManager()
        self.mngr.setHost(active=True)
        conn = self.mngr.getConnection()
        fakehttp(conn, getData("schema.xml"))  # fake schema response
        self.mngr.getSchema()  # read and cache the schema
        self.proc = SolrIndexProcessor(self.mngr)
        config = getConfig()
        config.atomic_updates = True

    def tearDown(self):
        self.mngr.closeConnection()
        self.mngr.setHost(active=False)

    def testPrepareData(self):
        data = {"allowedRolesAndUsers": ["user:test_user_1_", "user:portal_owner"]}
        prepareData(data)
        self.assertEqual(
            data, {"allowedRolesAndUsers": ["user$test_user_1_", "user$portal_owner"]}
        )

    def testLanguageParameterHandling(self):
        # empty strings are replaced...
        data = {"Language": ["en", ""]}
        prepareData(data)
        self.assertEqual(data, {"Language": ["en", "any"]})
        data = {"Language": ""}
        prepareData(data)
        self.assertEqual(data, {"Language": "any"})
        # for other indices this shouldn't happen...
        data = {"Foo": ["en", ""]}
        prepareData(data)
        self.assertEqual(data, {"Foo": ["en", ""]})

    def testIndexObject(self):
        response = getData("add_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)
        # indexing sends data
        self.proc.index(Foo(id="500", name="python test doc"))
        self.assertEqual(
            sortFields(str(output).encode("utf-8")),
            getData("add_request.txt").rstrip(b"\n"),
        )

    def testIndexAccessorRaises(self):
        response = getData("add_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)

        def brokenfunc():
            raise ValueError

        self.proc.index(
            Foo(id="500", name="python test doc", text=brokenfunc)
        )  # indexing sends data
        self.assertEqual(
            sortFields(str(output).encode("utf-8")),
            getData("add_request.txt").rstrip(b"\n"),
        )

    def testPartialIndexObject(self):
        foo = Foo(id="500", name="foo", price=42.0)
        # first index all attributes...
        response = getData("add_response.txt")
        output = fakehttp(self.mngr.getConnection(), response)
        self.proc.index(foo)
        self.assert_(
            str(output).find('<field name="price" update="set">42.0</field>') > 0,
            '"price" data not found',
        )
        # then only a subset...
        response = getData("add_response.txt")
        output = fakehttp(self.mngr.getConnection(), response)
        self.proc.index(foo, attributes=["id", "name"])
        output = str(output)
        self.assert_(
            output.find('<field name="name" update="set">foo</field>') > 0,
            '"name" data not found',
        )
        # at this point we'd normally check for a partial update:
        self.assertEqual(output.find("price"), -1, '"price" data found?')
        self.assertEqual(output.find("42"), -1, '"price" data found?')

    def testDateIndexing(self):
        foo = Foo(
            id="zeidler",
            name="andi",
            cat="nerd",
            timestamp=DateTime("May 11 1972 03:45:59.999730 GMT"),
        )
        response = getData("add_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)
        self.proc.index(foo)
        required = (
            '<field name="timestamp" update="set">' "1972-05-11T03:45:59.999Z</field>"
        )
        self.assert_(str(output).find(required) > 0, '"date" data not found')

    def testDateIndexingWithPythonDateTime(self):
        foo = Foo(
            id="gerken",
            name="patrick",
            cat="nerd",
            timestamp=datetime(1980, 9, 29, 14, 0o2, 59, 999730),
        )
        response = getData("add_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)
        self.proc.index(foo)
        required = (
            '<field name="timestamp" update="set">' "1980-09-29T14:02:59.999Z</field>"
        )
        self.assert_(str(output).find(required) > 0, '"date" data not found')

    def testDateIndexingWithPythonDate(self):
        foo = Foo(
            id="brand", name="jan-carel", cat="nerd", timestamp=date(1982, 8, 0o5)
        )
        response = getData("add_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)
        self.proc.index(foo)
        required = (
            '<field name="timestamp" update="set">' "1982-08-05T00:00:00.000Z</field>"
        )
        self.assert_(str(output).find(required) > 0, '"date" data not found')

    def testReindexObject(self):
        response = getData("add_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)
        # reindexing sends data
        self.proc.reindex(Foo(id="500", name="python test doc"))
        self.assertEqual(
            sortFields(str(output).encode("utf-8")),
            getData("add_request.txt").rstrip(b"\n"),
        )

    def testUnindexObject(self):
        response = getData("delete_response.txt")
        # fake response
        output = fakehttp(self.mngr.getConnection(), response)
        # unindexing sends data
        self.proc.unindex(Foo(id="500", name="python test doc"))
        self.assertEqual(
            str(output), getData("delete_request.txt").decode("utf-8").rstrip("\n")
        )

    def testCommit(self):
        response = getData("commit_response.txt")
        # fake response
        output = fakehttp(self.mngr.getConnection(), response)
        # committing sends data
        self.proc.commit()
        self.assertEqual(
            str(output), getData("commit_request.txt").decode("utf-8").rstrip("\n")
        )

    def testNoIndexingWithoutAllRequiredFields(self):
        response = getData("dummy_response.txt")
        # fake add response
        output = fakehttp(self.mngr.getConnection(), response)
        # indexing sends data
        self.proc.index(Foo(id="500"))
        self.assertEqual(str(output), "")

    def testIndexerMethods(self):
        class Bar(Foo):
            def cat(self):
                return "nerd"

            def price(self):
                raise AttributeError("price")

        foo = Bar(id="500", name="foo")
        # raising the exception should keep the attribute from being indexed
        response = getData("add_response.txt")
        output = fakehttp(self.mngr.getConnection(), response)
        self.proc.index(foo)
        output = str(output)
        self.assertTrue(
            output.find('<field name="cat" update="set">nerd</field>') > 0,
            '"cat" data not found',
        )
        self.assertEqual(output.find("price"), -1, '"price" data found?')


class RobustnessTests(TestCase):

    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def setUp(self):
        self.mngr = SolrConnectionManager()
        self.mngr.setHost(active=True)
        self.conn = self.mngr.getConnection()
        self.proc = SolrIndexProcessor(self.mngr)
        self.log = []  # catch log messages...

        def logger(*args):
            self.log.extend(args)

        logger_indexer.warning = logger
        config = getConfig()
        config.atomic_updates = True

    def tearDown(self):
        self.mngr.closeConnection()
        self.mngr.setHost(active=False)

    def testIndexingWithUniqueKeyMissing(self):
        # fake schema response
        fakehttp(self.conn, getData("simple_schema.xml"))
        # read and cache the schema
        self.mngr.getSchema()
        response = getData("add_response.txt")
        output = fakehttp(self.conn, response)  # fake add response
        foo = Foo(id="500", name="foo")
        # indexing sends data
        self.proc.index(foo)
        # nothing happened...
        self.assertEqual(len(output), 0)
        self.assertEqual(
            self.log, ["schema is missing unique key, skipping indexing of %r", foo]
        )

    def testUnindexingWithUniqueKeyMissing(self):
        # fake schema response
        fakehttp(self.conn, getData("simple_schema.xml"))
        # read and cache the schema
        self.mngr.getSchema()
        response = getData("delete_response.txt")
        # fake delete response
        output = fakehttp(self.conn, response)
        foo = Foo(id="500", name="foo")
        # unindexing sends data
        self.proc.unindex(foo)
        # nothing happened...
        self.assertEqual(len(output), 0)
        self.assertEqual(
            self.log, ["schema is missing unique key, skipping unindexing of %r", foo]
        )


class FakeHTTPConnectionTests(TestCase):

    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def setUp(self):
        self.foo = Foo(id="500", name="python test doc")
        self.schema_request = "GET /solr/plone/admin/file/?file=schema.xml"
        config = getConfig()
        config.atomic_updates = True

    def testSingleRequest(self):
        mngr = SolrConnectionManager(active=True)
        output = fakehttp(mngr.getConnection(), getData("schema.xml"))
        mngr.getSchema()
        mngr.closeConnection()
        self.failUnless(output.get().decode("utf-8").startswith(self.schema_request))

    def testTwoRequests(self):
        mngr = SolrConnectionManager(active=True)
        proc = SolrIndexProcessor(mngr)
        output = fakehttp(
            mngr.getConnection(), getData("schema.xml"), getData("add_response.txt")
        )
        proc.index(self.foo)
        mngr.closeConnection()
        self.assertEqual(len(output), 2)
        self.failUnless(output.get().decode("utf-8").startswith(self.schema_request))
        self.assertEqual(
            sortFields(output.get()), getData("add_request.txt").rstrip(b"\n")
        )

    def testThreeRequests(self):
        mngr = SolrConnectionManager(active=True)
        proc = SolrIndexProcessor(mngr)
        output = fakehttp(
            mngr.getConnection(),
            getData("schema.xml"),
            getData("add_response.txt"),
            getData("delete_response.txt"),
        )
        proc.index(self.foo)
        proc.unindex(self.foo)
        mngr.closeConnection()
        self.assertEqual(len(output), 3)
        self.failUnless(output.get().decode("utf-8").startswith(self.schema_request))
        self.assertEqual(
            sortFields(output.get()), getData("add_request.txt").rstrip(b"\n")
        )
        self.assertEqual(output.get(), getData("delete_request.txt").rstrip(b"\n"))

    def testFourRequests(self):
        mngr = SolrConnectionManager(active=True)
        proc = SolrIndexProcessor(mngr)
        output = fakehttp(
            mngr.getConnection(),
            getData("schema.xml"),
            getData("add_response.txt"),
            getData("delete_response.txt"),
            getData("commit_response.txt"),
        )
        proc.index(self.foo)
        proc.unindex(self.foo)
        proc.commit()
        mngr.closeConnection()
        self.assertEqual(len(output), 4)
        self.failUnless(output.get().decode("utf-8").startswith(self.schema_request))
        self.assertEqual(
            sortFields(output.get()), getData("add_request.txt").rstrip(b"\n")
        )
        self.assertEqual(output.get(), getData("delete_request.txt").rstrip(b"\n"))
        self.assertEqual(output.get(), getData("commit_request.txt").rstrip(b"\n"))

    def testExtraRequest(self):
        # basically the same as `testThreeRequests`, except it
        # tests adding fake responses consecutively
        mngr = SolrConnectionManager(active=True)
        proc = SolrIndexProcessor(mngr)
        conn = mngr.getConnection()
        output = fakehttp(conn, getData("schema.xml"))
        fakemore(conn, getData("add_response.txt"))
        proc.index(self.foo)
        fakemore(conn, getData("delete_response.txt"))
        proc.unindex(self.foo)
        mngr.closeConnection()
        self.assertEqual(len(output), 3)
        self.failUnless(output.get().decode("utf-8").startswith(self.schema_request))
        self.assertEqual(
            sortFields(output.get()), getData("add_request.txt").rstrip(b"\n")
        )
        self.assertEqual(output.get(), getData("delete_request.txt").rstrip(b"\n"))


class ThreadedConnectionTests(TestCase):

    layer = COLLECTIVE_SOLR_MOCK_REGISTRY_FIXTURE

    def testLocalConnections(self):
        config = getConfig()
        config.atomic_updates = True
        mngr = SolrConnectionManager(active=True)
        proc = SolrIndexProcessor(mngr)
        mngr.setHost(active=True)
        schema = getData("schema.xml")
        log = []

        def runner():
            # fake schema response on solr connection - caches the schema
            fakehttp(mngr.getConnection(), getData("schema.xml"))
            mngr.getConnection().get_schema()

            fakehttp(mngr.getConnection(), schema)  # fake schema response
            # read and cache the schema
            mngr.getSchema()
            response = getData("add_response.txt")
            # fake add response
            output = fakehttp(mngr.getConnection(), response)
            # indexing sends data
            proc.index(Foo(id="500", name="python test doc"))
            mngr.closeConnection()
            log.append(str(output))
            log.append(proc)
            log.append(mngr.getConnection())

        # after the runner was set up, another thread can be created and
        # started;  its output should contain the proper indexing request,
        # whereas the main thread's connection remain idle;  the latter
        # cannot be checked directly, but the connection object would raise
        # an exception if it was used to send a request without setting up
        # a fake response beforehand...
        thread = Thread(target=runner)
        thread.start()
        thread.join()
        conn = mngr.getConnection()  # get this thread's connection
        fakehttp(conn, schema)  # fake schema response
        mngr.getSchema()  # read and cache the schema
        mngr.closeConnection()
        mngr.setHost(active=False)
        self.assertEqual(len(log), 3)
        self.assertEqual(
            sortFields(log[0].encode("utf-8")), getData("add_request.txt").rstrip(b"\n")
        )
        self.failUnless(isinstance(log[1], SolrIndexProcessor))
        self.failUnless(isinstance(log[2], SolrConnection))
        self.failUnless(isinstance(proc, SolrIndexProcessor))
        self.failUnless(isinstance(conn, SolrConnection))
        self.assertEqual(log[1], proc)  # processors should be the same...
        self.assertNotEqual(log[2], conn)  # but not the connections
