# -*- coding: utf-8 -*-


class SolrException(Exception):
    """Base class where all other exceptions from collective.solr derive from
    """


class SolrInactiveException(SolrException):
    """An exception indicating the solr integration is not activated"""


class FallBackException(SolrException):
    """Exception indicating the dispatcher should fall back to searching
       the portal catalog
    """


class SolrConnectionException(SolrException):
    """An exception thrown by solr connections"""

    def __init__(self, httpcode='000', reason=None, body=None):
        self.httpcode = httpcode
        self.reason = reason
        self.body = body

    def __repr__(self):
        return 'HTTP code=%s, Reason=%s, body=%s' % (
            self.httpcode, self.reason, self.body
        )

    def __str__(self):
        return 'HTTP code=%s, reason=%s' % (self.httpcode, self.reason)
