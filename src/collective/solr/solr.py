# http://svn.apache.org/repos/asf/lucene/solr/trunk/client/python/solr.py

# Licensed to the Apache Software Foundation (ASF) under one or more
# contributor license agreements.  See the NOTICE file distributed with
# this work for additional information regarding copyright ownership.
# The ASF licenses this file to You under the Apache License, Version 2.0
# (the "License"); you may not use this file except in compliance with
# the License.  You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# A simple Solr client for python.
#
# quick examples on use:
#
# from collective.solr.solr import *
# c = SolrConnection(host='localhost:8983', persistent=True)
# c.add(id='500',name='python test doc')
# c.commit()
# c.search(q='id:[* TO *]', wt='python', rows='10',indent='on')
# c.delete('123')
# c.commit()

import base64
import codecs
import socket
from copy import deepcopy
from logging import getLogger
from xml.etree.cElementTree import fromstring
from xml.sax.saxutils import escape

import six
import six.moves.http_client
import six.moves.urllib.parse
import six.moves.urllib.request
from collective.solr.exceptions import SolrConnectionException
from collective.solr.parser import SolrSchema
from collective.solr.utils import getConfig, translation_map
from plone.dexterity.utils import safe_unicode
from requests_toolbelt import MultipartEncoder

logger = getLogger(__name__)


class SolrConnection:
    def __init__(
        self,
        host="localhost:8983",
        solrBase="/solr/plone",
        persistent=True,
        postHeaders={},
        timeout=None,
        login=None,
        password=None,
    ):
        self.host = host
        self.solrBase = str(solrBase)
        self.persistent = persistent
        self.reconnects = 0
        self.encoder = codecs.getencoder("utf-8")
        # responses from Solr will always be in UTF-8
        self.decoder = codecs.getdecoder("utf-8")
        # a real connection to the server is not opened at this point.
        self.conn = six.moves.http_client.HTTPConnection(self.host, timeout=timeout)
        # self.conn.set_debuglevel(1000000)
        self.login = login
        self.auth_headers = {}
        if login and password:
            credentials = "{0}:{1}".format(login, password)
            authorization = base64.b64encode(credentials.encode("ascii"))
            self.auth_headers["Authorization"] = "Basic {0}".format(
                authorization.decode("ascii")
            )
        self.xmlbody = []
        self.xmlheaders = {"Content-Type": "text/xml; charset=utf-8"}
        self.xmlheaders.update(postHeaders)
        self.xmlheaders.update(self.auth_headers)
        if not self.persistent:
            self.xmlheaders["Connection"] = "close"
        self.formheaders = {
            "Content-Type": "application/x-www-form-urlencoded; charset=utf-8",
        }
        self.formheaders.update(self.auth_headers)
        if not self.persistent:
            self.formheaders["Connection"] = "close"

    def __str__(self):
        xmlheaders = deepcopy(self.xmlheaders)
        if "Authorization" in xmlheaders:
            xmlheaders["Authorization"] = "Basic ***"
        return (
            "SolrConnection{host=%s, solrBase=%s, persistent=%s, "
            "postHeaders=%s, reconnects=%s, login=%s, password=%s}"
            % (
                self.host,
                self.solrBase,
                self.persistent,
                xmlheaders,
                self.reconnects,
                self.login,
                self.auth_headers and "***" or None,
            )
        )

    def __reconnect(self):
        self.reconnects += 1
        self.conn.close()
        self.conn.connect()

    reset = __reconnect

    def close(self):
        self.conn.close()

    def __errcheck(self, rsp):
        if rsp.status != 200:
            ex = SolrConnectionException(rsp.status, rsp.reason)
            try:
                ex.body = rsp.read()
            except:  # noqa
                pass
            raise ex
        return rsp

    def setTimeout(self, timeout):
        """set a timeout value for the currently open connection"""
        logger.debug("setting socket timeout on %r: %s", self, timeout)
        self.conn.timeout = timeout

    def doPost(self, url, body, headers):
        return self.doGetOrPost("POST", url, body, headers)

    def doGet(self, url, headers):
        return self.doGetOrPost("GET", url, "", headers)

    def doGetOrPost(self, method, url, body, headers):
        if not isinstance(body, (six.binary_type, MultipartEncoder)):
            body = body.encode("utf-8")
        try:
            self.conn.request(method, url, body, headers)
            return self.__errcheck(self.conn.getresponse())
        except (
            socket.error,
            six.moves.http_client.CannotSendRequest,
            six.moves.http_client.ResponseNotReady,
            six.moves.http_client.BadStatusLine,
        ):
            # Reconnect in case the connection was broken from the server
            # going down, the server timing out our persistent connection, or
            # another network failure. Also catch httplib.CannotSendRequest,
            # httlib.ResponseNotReady and httlib.BadStatusLine because the
            # HTTPConnection object can get in a bad state (seems like they
            # might be "ghosted" in the zodb).
            self.__reconnect()
            self.conn.request(method, url, body, headers)
            return self.__errcheck(self.conn.getresponse())

    def doUpdateXML(self, request):
        # solr will support abort/rollback only from version 1.4, so
        # for now we delay sending the xml until the commit...
        # see http://issues.apache.org/jira/browse/SOLR-670
        logger.debug("storing xml request for later: %r", request)
        self.xmlbody.append(request)

    def flush(self):
        """send out the stored requests to solr"""
        count = 0
        responses = []
        for request in self.xmlbody:
            try:
                responses.append(self.doSendXML(request))
            except (SolrConnectionException, socket.error):
                logger.exception("exception during request %r", request)
            count += len(request)
        logger.debug("flushed out %d bytes in %d requests", count, len(self.xmlbody))
        del self.xmlbody[:]
        return responses

    def doSendXML(self, request):
        try:
            rsp = self.doPost(self.solrBase + "/update", request, self.xmlheaders)
            data = rsp.read()
        finally:
            if not self.persistent:
                self.conn.close()
        # detect old-style error response (HTTP response code of
        # 200 with a non-zero status.
        parsed = fromstring(self.decoder(data)[0])
        status = parsed.attrib.get("status", 0)
        if status != 0:
            reason = parsed.documentElement.firstChild.nodeValue
            raise SolrConnectionException(rsp.status, reason)
        return parsed

    def escapeVal(self, val):
        if not isinstance(val, six.text_type):
            try:
                val = six.text_type(val)
            except UnicodeDecodeError:
                val = safe_unicode(val)
        if six.PY2:
            val = val.encode("utf-8")
        escaped_val = escape(val.translate(translation_map))
        if isinstance(escaped_val, six.binary_type):
            escaped_val = escaped_val.decode("utf-8")
        return escaped_val

    def escapeKey(self, key):
        if not isinstance(key, six.text_type):
            key = six.text_type(key)
        key = key.replace("&", "&amp;")
        key = key.replace('"', "&quot;")
        return key

    def delete(self, id):
        xstr = "<delete><id>%s</id></delete>" % self.escapeVal(id)
        return self.doUpdateXML(xstr)

    def deleteByQuery(self, query):
        xstr = "<delete><query>%s</query></delete>" % self.escapeVal(query)
        return self.doUpdateXML(xstr)

    def get_schema(self):
        """Memoized access to Solr Schema.

        We need to know which one is the uniqueKey in the add() method below,
        but don't want to hit Solr with a request for the schema on every
        single add().
        """
        if not hasattr(self, "_schema"):
            self._schema = self.getSchema()
        return self._schema

    def add(self, boost_values=None, atomic_updates=True, **fields):
        solr_config = getConfig()
        atomic_updates_enabled = getattr(solr_config, "atomic_updates", atomic_updates)

        schema = self.get_schema()
        uniqueKey = schema.get("uniqueKey", None)
        if uniqueKey is None:
            raise Exception("Could not get uniqueKey from Solr schema")

        if uniqueKey not in fields:
            logger.warning(
                "uniqueKey '%s' missing for item %s, skipping" % (uniqueKey, fields)
            )
            return

        latlon_fields = [
            field["name"]
            for field in schema.fields
            if field["class"] == "solr.LatLonPointSpatialField"
        ]

        within = fields.pop("commitWithin", None)
        if within:
            lst = ['<add commitWithin="%s">' % str(within)]
        else:
            lst = ["<add>"]
        if boost_values is None:
            boost_values = {}
        if "" in boost_values:  # boost value for the entire document
            lst.append('<doc boost="%s">' % boost_values[""])
        else:
            lst.append("<doc>")

        for f, v in fields.items():

            # Add update="set" attribute to each field except for the uniqueKey
            # field.
            if f == uniqueKey:
                tmpl = '<field name="%s">%%s</field>' % self.escapeKey(f)
                lst.append(tmpl % self.escapeVal(v))
                continue

            # geolocation need to be explicitly deleted. They can't index
            # None or empty strings.
            if f in latlon_fields and not v:
                tmpl = '<field name="%s" update="set" null="true"/>'
                lst.append(tmpl % (self.escapeKey(f)))
                continue
            if f in boost_values:
                tmpl = '<field name="%s" boost="%s" update="set">%%s</field>'
                tmpl = tmpl % (self.escapeKey(f), boost_values[f])
            else:
                tmpl = '<field name="%s" update="set">%%s</field>'
                tmpl = tmpl % self.escapeKey(f)

            if not atomic_updates_enabled:
                # Remove update="set", since it breaks the index time boosting.
                tmpl = tmpl.replace(' update="set"', "")

            if isinstance(v, (list, tuple)):  # multi-valued
                for value in v:
                    lst.append(tmpl % self.escapeVal(value))
                if not v:
                    tmpl = '<field name="%s" update="set" null="true"/>'
                    lst.append(tmpl % (self.escapeKey(f)))
            else:
                lst.append(tmpl % self.escapeVal(v))
        lst.append("</doc>")
        lst.append("</add>")
        xstr = "".join(lst)

        if self.conn.debuglevel > 0:
            logger.info("Update message:\n" + xstr)

        return self.doUpdateXML(xstr)

    def commit(self, waitSearcher=True, optimize=False, soft=False):
        data = {
            "committype": optimize and "optimize" or "commit",
            "nowait": not waitSearcher and ' waitSearcher="false"' or "",
            "soft": soft and ' softCommit="true"' or "",
        }
        xstr = "<%(committype)s%(soft)s%(nowait)s/>" % data
        self.doUpdateXML(xstr)
        return self.flush()

    def abort(self):
        # solr will support abort/rollback only from version 1.4, so
        # for now we delay sending the xml until the commit (see above),
        # which is why we don't have to send anything to abort...
        # see http://issues.apache.org/jira/browse/SOLR-670
        logger.debug("aborting %d requests: %r", len(self.xmlbody), self.xmlbody)
        del self.xmlbody[:]

    def search(self, **params):
        request_handler = params.get("request_handler", "select")
        if "request_handler" in params:
            del params["request_handler"]
        for key, value in params.items():
            if isinstance(value, six.text_type):
                params[key] = value.encode("utf-8")
        request = six.moves.urllib.parse.urlencode(params, doseq=True)
        logger.debug("sending request: %s" % request)
        try:
            response = self.doPost(
                "%s/%s" % (self.solrBase, request_handler), request, self.formheaders
            )
        finally:
            if not self.persistent:
                self.conn.close()
        return response

    def getSchema(self):
        schema_url = "%s/admin/file/?file=schema.xml"
        # schema_url = '%s/admin/file/?file=managed-schema'
        logger.debug("getting schema from: %s", schema_url % self.solrBase)
        try:
            self.conn.request(
                "GET", schema_url % self.solrBase, headers=self.auth_headers
            )
            response = self.conn.getresponse()
        except (
            socket.error,
            six.moves.http_client.CannotSendRequest,
            six.moves.http_client.ResponseNotReady,
            six.moves.http_client.BadStatusLine,
        ):
            # see `doPost` method for more info about these exceptions
            self.__reconnect()
            self.conn.request(
                "GET", schema_url % self.solrBase, headers=self.auth_headers
            )
            response = self.conn.getresponse()

        if response.status == 200:
            xml = response.read().decode("utf-8")
            return SolrSchema(xml.strip())

        self.__errcheck(response)  # raise a SolrConnectionException
