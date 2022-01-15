import os
from logging import getLogger
from socket import error

import six
from collective.solr.interfaces import ISolrConnectionManager, IZCMLSolrConnectionConfig
from collective.solr.local import getLocal, setLocal
from collective.solr.solr import SolrConnection
from collective.solr.utils import getConfig, isActive
from plone.registry.interfaces import IRegistry
from six.moves.http_client import CannotSendRequest, ResponseNotReady
from zope.component import getUtility, queryUtility
from zope.interface import implementer

logger = getLogger("collective.solr.manager")
marker = object()


def none_formatter(value):
    """Return `None` if value is considered as empty"""
    if not value:
        return
    return value


@implementer(IZCMLSolrConnectionConfig)
class ZCMLSolrConnectionConfig(object):
    """Connection values that can be configured through zcml"""

    def __init__(self, host, port, base):
        self.host = "%s:%d" % (host, port)
        self.base = base


@implementer(ISolrConnectionManager)
class SolrConnectionManager(object):
    """a thread-local connection manager for solr"""

    lock = False

    def __init__(self, active=None):
        if isinstance(active, bool):
            self.setHost(active=active)

    def setHost(self, active=False, host="localhost", port=8983, base="/solr/plone"):
        """set connection parameters"""
        config = getConfig()
        config.active = active
        config.host = six.text_type(host)
        config.port = port
        config.base = six.text_type(base)
        self.closeConnection(clearSchema=True)

    def closeConnection(self, clearSchema=False):
        """close the current connection, if any"""
        logger.debug("closing connection")
        conn = getLocal("connection")
        if conn is not None:
            conn.close()
            setLocal("connection", None)
        if clearSchema:
            setLocal("schema", None)

    def getConfigParameter(self, key, env_key=None, formatter=None):
        """Return config from environment variable or by default from registry"""
        if not env_key:
            # Transform registry to match environment variable key
            # collective.solr.variable become COLLECTIVE_SOLR_VARIABLE
            env_key = key.replace(".", "_").upper()
        registry = getUtility(IRegistry)
        value = os.getenv(env_key, registry[key])
        if formatter:
            return formatter(value)
        return value

    def getConnection(self):
        """returns an existing connection or opens one"""
        if not isActive():
            return None
        conn = getLocal("connection")
        if conn is not None:
            return conn

        zcmlconfig = queryUtility(IZCMLSolrConnectionConfig)
        config_host = self.getConfigParameter("collective.solr.host")
        config_login = self.getConfigParameter(
            "collective.solr.solr_login",
            env_key="COLLECTIVE_SOLR_LOGIN",
            formatter=none_formatter,
        )
        config_password = self.getConfigParameter(
            "collective.solr.solr_password",
            env_key="COLLECTIVE_SOLR_PASSWORD",
            formatter=none_formatter,
        )
        if zcmlconfig is not None:
            # use connection parameters defined in zcml...
            logger.debug("opening connection to %s", zcmlconfig.host)
            conn = SolrConnection(
                host=zcmlconfig.host,
                solrBase=zcmlconfig.base,
                persistent=True,
                login=config_login,
                password=config_password,
            )
            setLocal("connection", conn)
        elif config_host is not None:
            # otherwise use connection parameters defined in control panel...
            config_port = self.getConfigParameter("collective.solr.port", formatter=int)
            config_base = self.getConfigParameter("collective.solr.base")
            host = "%s:%d" % (config_host, config_port)
            logger.debug("opening connection to %s", host)
            conn = SolrConnection(
                host=host,
                solrBase=config_base,
                persistent=True,
                login=config_login,
                password=config_password,
            )
            setLocal("connection", conn)
        return conn

    def getSchema(self):
        """returns the currently used schema or fetches it"""
        schema = getLocal("schema")
        if schema is None:
            conn = self.getConnection()
            if conn is not None:
                logger.debug("getting schema from solr")
                self.setSearchTimeout()
                try:
                    schema = conn.get_schema()
                    setLocal("schema", schema)
                except (error, CannotSendRequest, ResponseNotReady):
                    logger.exception("exception while getting schema")
        return schema

    def setTimeout(self, timeout, lock=marker):
        """set the timeout on the current (or to be opened) connection
        to the given value"""
        update = not self.lock  # update if not locked...
        if lock is not marker:
            self.lock = bool(lock)
            update = True  # ...or changed
            logger.debug("%ssetting timeout lock", lock and "" or "re")
        if update:
            conn = self.getConnection()
            if conn is not None:
                logger.debug("setting timeout to %s", timeout)
                conn.setTimeout(timeout)

    def setIndexTimeout(self):
        """set the timeout on the current (or to be opened) connection
        to the value specified for indexing operations"""
        registry = getUtility(IRegistry)
        index_timeout = registry["collective.solr.index_timeout"]
        self.setTimeout(index_timeout or None)

    def setSearchTimeout(self):
        """set the timeout on the current (or to be opened) connection
        to the value specified for search operations"""
        registry = getUtility(IRegistry)
        search_timeout = registry["collective.solr.search_timeout"]
        self.setTimeout(search_timeout or None)
