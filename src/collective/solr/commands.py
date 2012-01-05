from cPickle import dumps
from cPickle import loads
import datetime
import logging
import os
import os.path
from os import listdir
from os.path import join
from struct import pack, unpack
import sys

from Acquisition import aq_base
from Acquisition import aq_get
from Acquisition import aq_parent
from BTrees.IIBTree import IISet
from BTrees.IIBTree import IITreeSet
from collective.solr.indexer import datehandler
from collective.solr.interfaces import ISolrConnectionManager
from DateTime import DateTime
from zope.component import queryUtility
from zope.i18nmessageid import Message
from zope.site.hooks import setHooks
from zope.site.hooks import setSite

logger = logging.getLogger()


def _get_site(app, args):
    name = None
    if len(args) > 0:
        name = args[0]
        if name not in app:
            logger.error("Specified site '%s' not found in database." % name)
            sys.exit(1)
    else:
        from Products.CMFPlone.Portal import PloneSite
        for k, v in app.items():
            if isinstance(v, PloneSite):
                name = k
                break
    if not name:
        logger.error("No Plone site found in database root.")
        sys.exit(1)
    site = getattr(app, name)
    setHooks()
    setSite(site)
    return site


def _solr_connection():
    manager = queryUtility(ISolrConnectionManager)
    conn = manager.getConnection()
    logger.info('Opened Solr connection to %s' % conn.host)
    return conn


def solr_clear_index(app, args):
    """Removes all data from a Solr index. Equivalent to removing the
    `data/index` directory while Solr is stopped. You can optionally specify
    the id of the Plone site as the first command line argument.
    """
    _get_site(app, args) # calls setSite so queryUtility works
    conn = _solr_connection()
    conn.deleteByQuery('[* TO *]')
    conn.commit(optimize=True)
    conn.close()
