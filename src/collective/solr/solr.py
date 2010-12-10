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

import httplib
import socket
from elementtree.ElementTree import fromstring
from xml.sax.saxutils import escape
import codecs
import urllib
from collective.solr.parser import SolrSchema
from collective.solr.timeout import HTTPConnectionWithTimeout
from collective.solr.utils import translation_map

from logging import getLogger
logger = getLogger(__name__)


class SolrException(Exception):
    """ An exception thrown by solr connections """

    def __init__(self, httpcode, reason=None, body=None):
        self.httpcode = httpcode
        self.reason = reason
        self.body = body

    def __repr__(self):
        return 'HTTP code=%s, Reason=%s, body=%s' % (
                    self.httpcode, self.reason, self.body)

    def __str__(self):
        return 'HTTP code=%s, reason=%s' % (self.httpcode, self.reason)


class SolrConnection:

    def __init__(self, host='localhost:8983', solrBase='/solr',
                 persistent=True, postHeaders={}, timeout=None):
        self.host = host
        self.solrBase = solrBase
        self.persistent = persistent
        self.reconnects = 0
        self.encoder = codecs.getencoder('utf-8')
        # responses from Solr will always be in UTF-8
        self.decoder = codecs.getdecoder('utf-8')
        # a real connection to the server is not opened at this point.
        self.conn = HTTPConnectionWithTimeout(self.host, timeout=timeout)
        # self.conn.set_debuglevel(1000000)
        self.xmlbody = []
        self.xmlheaders = {'Content-Type': 'text/xml; charset=utf-8'}
        self.xmlheaders.update(postHeaders)
        if not self.persistent:
            self.xmlheaders['Connection']='close'
        self.formheaders = {'Content-Type':
            'application/x-www-form-urlencoded; charset=utf-8'}
        if not self.persistent:
            self.formheaders['Connection']='close'

    def __str__(self):
        return ('SolrConnection{host=%s, solrBase=%s, persistent=%s, '
            'postHeaders=%s, reconnects=%s}' % (self.host, self.solrBase,
            self.persistent, self.xmlheaders, self.reconnects))

    def __reconnect(self):
        self.reconnects += 1
        self.conn.close()
        self.conn.connect()

    reset = __reconnect

    def close(self):
        self.conn.close()

    def __errcheck(self, rsp):
        if rsp.status != 200:
            ex = SolrException(rsp.status, rsp.reason)
            try:
                ex.body = rsp.read()
            except:
                pass
            raise ex
        return rsp

    def setTimeout(self, timeout):
        """ set a timeout value for the currently open connection """
        logger.debug('setting socket timeout on %r: %s', self, timeout)
        self.conn.setTimeout(timeout)

    def doPost(self, url, body, headers):
        try:
            self.conn.request('POST', url, body, headers)
            return self.__errcheck(self.conn.getresponse())
        except (socket.error, httplib.CannotSendRequest,
            httplib.ResponseNotReady, httplib.BadStatusLine):
            # Reconnect in case the connection was broken from the server
            # going down, the server timing out our persistent connection, or
            # another network failure. Also catch httplib.CannotSendRequest,
            # httlib.ResponseNotReady and httlib.BadStatusLine because the
            # HTTPConnection object can get in a bad state (seems like they
            # might be "ghosted" in the zodb).
            self.__reconnect()
            self.conn.request('POST', url, body, headers)
            return self.__errcheck(self.conn.getresponse())

    def doUpdateXML(self, request):
        # solr will support abort/rollback only from version 1.4, so
        # for now we delay sending the xml until the commit...
        # see http://issues.apache.org/jira/browse/SOLR-670
        logger.debug('storing xml request for later: %r', request)
        self.xmlbody.append(request)

    def flush(self):
        """ send out the stored requests to solr """
        count = 0
        responses = []
        for request in self.xmlbody:
            try:
                responses.append(self.doSendXML(request))
            except (SolrException, socket.error):
                logger.exception('exception during request %r', request)
            count += len(request)
        logger.debug('flushed out %d bytes in %d requests',
            count, len(self.xmlbody))
        del self.xmlbody[:]
        return responses

    def doSendXML(self, request):
        try:
            rsp = self.doPost(self.solrBase+'/update', request,
                self.xmlheaders)
            data = rsp.read()
        finally:
            if not self.persistent:
                self.conn.close()
        #detect old-style error response (HTTP response code of
        #200 with a non-zero status.
        parsed = fromstring(self.decoder(data)[0])
        status = parsed.attrib.get('status', 0)
        if status != 0:
            reason = parsed.documentElement.firstChild.nodeValue
            raise SolrException(rsp.status, reason)
        return parsed

    def escapeVal(self, val):
        if isinstance(val, unicode):
            val = val.encode('utf-8')
        else:
            val = str(val)
        return escape(val.translate(translation_map))

    def escapeKey(self, key):
        if isinstance(key, unicode):
            key = key.encode('utf-8')
        else:
            key = str(key)
        key = key.replace("&", "&amp;")
        key = key.replace('"', "&quot;")
        return key

    def delete(self, id):
        xstr = '<delete><id>%s</id></delete>' % self.escapeVal(id)
        return self.doUpdateXML(xstr)

    def deleteByQuery(self, query):
        xstr = '<delete><query>%s</query></delete>' % self.escapeVal(query)
        return self.doUpdateXML(xstr)

    def add(self, boost_values=None, **fields):
        within = fields.pop('commitWithin', None)
        if within:
            lst = ['<add commitWithin="%s">' % str(within)]
        else:
            lst = ['<add>']
        if boost_values is None:
            boost_values = {}
        if '' in boost_values:      # boost value for the entire document
            lst.append('<doc boost="%s">' % boost_values[''])
        else:
            lst.append('<doc>')
        for f, v in fields.items():
            if f in boost_values:
                tmpl = '<field name="%s" boost="%s">%%s</field>' % (
                    self.escapeKey(f), boost_values[f])
            else:
                tmpl = '<field name="%s">%%s</field>' % self.escapeKey(f)
            if isinstance(v, (list, tuple)): # multi-valued
                for value in v:
                    lst.append(tmpl % self.escapeVal(value))
            else:
                lst.append(tmpl % self.escapeVal(v))
        lst.append('</doc>')
        lst.append('</add>')
        xstr = ''.join(lst)
        return self.doUpdateXML(xstr)

    def commit(self, waitFlush=True, waitSearcher=True, optimize=False):
        data = {'committype': optimize and 'optimize' or 'commit',
                'nowait': not waitSearcher and ' waitSearcher="false"' or '',
                'noflush': not waitFlush and not waitSearcher and \
                    ' waitFlush="false"' or ''}
        xstr = '<%(committype)s%(noflush)s%(nowait)s/>' % data
        self.doUpdateXML(xstr)
        return self.flush()

    def abort(self):
        # solr will support abort/rollback only from version 1.4, so
        # for now we delay sending the xml until the commit (see above),
        # which is why we don't have to send anything to abort...
        # see http://issues.apache.org/jira/browse/SOLR-670
        logger.debug('aborting %d requests: %r',
            len(self.xmlbody), self.xmlbody)
        del self.xmlbody[:]

    def search(self, **params):
        request = urllib.urlencode(params, doseq=True)
        try:
            response = self.doPost('%s/select' % self.solrBase, request,
                self.formheaders)
        finally:
            if not self.persistent:
                self.conn.close()
        return response

    def getSchema(self):
        schema_urls = ('%s/admin/file/?file=schema.xml',        # solr 1.3
                       '%s/admin/get-file.jsp?file=schema.xml') # solr 1.2
        for url in schema_urls:
            logger.debug('getting schema from: %s', url % self.solrBase)
            try:
                self.conn.request('GET', url % self.solrBase)
                response = self.conn.getresponse()
            except (socket.error, httplib.CannotSendRequest,
                httplib.ResponseNotReady, httplib.BadStatusLine):
                # see `doPost` method for more info about these exceptions
                self.__reconnect()
                self.conn.request('GET', url % self.solrBase)
                response = self.conn.getresponse()
            if response.status == 200:
                xml = response.read()
                return SolrSchema(xml.strip())
            self.__reconnect()          # force a new connection for each url
        self.__errcheck(response)       # raise a solrexception
