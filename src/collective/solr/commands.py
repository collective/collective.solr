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


def _data_dir(siteid):
    from App.config import getConfiguration
    clienthome = getConfiguration().clienthome
    d = join(clienthome, 'solr_dump_%s' % siteid.lower())
    logger.info("Using data directory: '%s'" % d)
    return d


def _enable_log():
    # Display all messages on stderr
    logger.setLevel(logging.INFO)
    logger.handlers[0].setLevel(logging.INFO)


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


def _log_batch(db, batch, i):
    if i % 10000 == 0:
        db.cacheMinimize()
        logger.info('Processed batch %s' % batch)
        batch += 1
    return batch


def _make_dir(path):
    if not os.path.exists(path):
        os.mkdir(path)


def _dump(data_dir, uid, data):
    # Data is stored in a directory structure with one directory level for
    # 1000 files each. There's one file per catalog record id.
    prefix, suffix = str(uid)[:-3], str(uid)[-3:]
    prefix_dir = join(data_dir, prefix)
    _make_dir(prefix_dir)
    filepath = join(prefix_dir, '%s.pickle' % suffix)
    # The file format is a fixed 8 byte length and a data payload of that
    # length. Multiple of these can appear in the same file. Data from later
    # segments will override information from earlier segments. The data is
    # pickles of dicts, consisting of an indexname to value mapping
    with open(filepath, 'ab', 10000) as fd:
        pdata = dumps(data, 1)
        header = pack('<I', len(pdata))
        fd.write(header)
        fd.write(pdata)


def _convert_value(indexname, value, date_index=False):
    # Missing support for string values representing booleans. Shouldn't be
    # an issue anymore with a dedicated BooleanIndex being available
    if not value or value == 'None':
        return None
    if isinstance(value, (IISet, IITreeSet)):
        value = tuple(value.keys())
    elif isinstance(value, (set, list, tuple)):
        value = tuple(value)
    elif isinstance(value, unicode):
        value = value.encode('utf-8')
    elif isinstance(value, Message):
        value = unicode(value).encode('utf-8')
    elif isinstance(value, (DateTime, datetime.datetime)):
        value = datehandler(value)
    elif date_index:
        if isinstance(value, int):
            value = datetime.datetime.utcfromtimestamp(value)
        value = datehandler(value)
    elif not isinstance(value, (bool, int, long, float, str)):
        logger.debug('Unsupported value: %s for index: %s' % (
            repr(value), indexname))
    return value


def solr_dump_catalog(app, args):
    """Dumps the catalog and metadata contents into a nested directory
    structure full of pickles containing the information in dict format.
    These can be updated by later re-runs and used to import the data via the
    `update_solr` command. You can optionally specify the id of the Plone site
    as the first command line argument.
    """
    _enable_log()
    db = app._p_jar.db()
    site = _get_site(app, args)
    data_dir = _data_dir(site.getId())
    _make_dir(data_dir)

    catalog = site.portal_catalog
    _catalog = catalog._catalog
    catalog_length = len(catalog)
    uids_get = _catalog.uids.get

    conn = _solr_connection()
    schema = conn.getSchema()
    wanted = set(schema.keys())
    # We need the data from path
    wanted.add('path')
    conn.close()

    logger.info('Process %s catalog items' % catalog_length)

    from collective.indexing.indexer import getOwnIndexMethod
    from collective.solr.indexer import indexable
    from collective.solr.utils import findObjects
    from plone.app.folder.nogopip import GopipIndex
    from Products.PluginIndexes.DateIndex.DateIndex import DateIndex
    from Products.PluginIndexes.DateRangeIndex import DateRangeIndex
    from Products.ZCTextIndex import WidCode
    from Products.ZCTextIndex.ZCTextIndex import ZCTextIndex

    indexes = catalog.indexes()
    indexes.sort()

    gopip_indexes = set()
    for indexname in indexes:
        if indexname in _catalog.schema:
            # There's no need to get metadata from the indexes
            continue
        if indexname not in wanted:
            # skip indexes not present in the Solr schema
            continue
        logger.info('Dumping index: %s' % indexname)
        index = _catalog.getIndex(indexname)
        if isinstance(index, DateRangeIndex.DateRangeIndex):
            # Solr cannot deal with range indexes directly
            continue
        if isinstance(index, ZCTextIndex):
            get_word = index.getLexicon().get_word
            wid_decode = WidCode.decode
            batch = 0
            for i, (uid, value) in enumerate(index.index._docwords.items()):
                batch = _log_batch(db, batch, i)
                words = ' '.join([get_word(w) for w in wid_decode(value)])
                _dump(data_dir, uid, {indexname: words})
        elif isinstance(index, GopipIndex):
            # happens last as it needs a full site traversal
            gopip_indexes.add(indexname)
            continue
        elif not hasattr(index, '_unindex'):
            logger.warn("Unsupported index '%s' without an _unindex." %
                indexname)
        else:
            date_index = isinstance(index, DateIndex)
            batch = 0
            for i, (uid, value) in enumerate(index._unindex.iteritems()):
                batch = _log_batch(db, batch, i)
                value = _convert_value(indexname, value, date_index)
                if value:
                    _dump(data_dir, uid, {indexname: value})

    # dump metadata
    logger.info('Dumping metadata records')
    batch = 0
    for i, uid in enumerate(_catalog.paths.iterkeys()):
        batch = _log_batch(db, batch, i)
        values = {}
        for k, v in _catalog.getMetadataForRID(uid).iteritems():
            definition = schema.get(k)
            if not definition:
                continue
            date_index = definition['class_'] == 'solr.TrieDateField'
            value = _convert_value(k, v, date_index)
            if value:
                values[k] = value
        _dump(data_dir, uid, values)

    # deal with GopipIndexes
    batch = 0
    logger.info('Traversing site to dump Gopip index information')
    for i, (path, obj) in enumerate(findObjects(site)):
        batch = _log_batch(db, batch, i)
        if not indexable(obj):
            continue
        elif getOwnIndexMethod(obj, 'indexObject') is not None:
            continue
        parent = aq_parent(obj)
        uid = uids_get('/'.join(obj.getPhysicalPath()), None)
        if uid is None:
            continue
        if hasattr(aq_base(parent), 'getObjectPosition'):
            pos = parent.getObjectPosition(path.split('/')[-1])
            data = {}
            for name in gopip_indexes:
                data[name] = pos
            _dump(data_dir, uid, data)
        else:
            data = {}
            for name in gopip_indexes:
                data[name] = 0
            _dump(data_dir, uid, data)
        if not getattr(aq_base(obj), 'isPrincipiaFolderish', False):
            # Remove non-folders from the cache immediately as we no longer
            # need them
            obj._p_deactivate()


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


def solr_import_dump(app, args):
    """Updates Solr with the data dumped via the dump_catalog command. You can
    optionally specify the id of the Plone site as the first command line
    argument.
    """
    _enable_log()

    from Testing import makerequest
    root = makerequest.makerequest(app)
    site = _get_site(root, args)
    site.setupCurrentSkin(site.REQUEST)
    boost_script = aq_get(site, 'solr_boost_index_values')

    conn = _solr_connection()
    data_dir = _data_dir(site.getId())
    for i, rid_prefix in enumerate(listdir(data_dir)):
        prefix_dir = join(data_dir, rid_prefix)
        if not os.path.isdir(prefix_dir):
            continue
        for suffix in listdir(prefix_dir):
            if suffix.endswith('.pickle'):
                data = {}
                with open(join(prefix_dir, suffix), 'rb', 10000) as fd:
                    while True:
                        header = fd.read(4)
                        if len(header) != 4:
                            break
                        length = unpack('<I', header)[0]
                        pdata = fd.read(length)
                        data.update(loads(pdata))

                # mangle EPI data into Solr representation
                path = data.get('path')
                tuple_path = path.split('/')
                data['physicalPath'] = path
                data['physicalDepth'] = len(tuple_path)
                data['parentPaths'] = ['/'.join(tuple_path[:n+1])
                    for n in xrange(1, len(tuple_path))]
                del data['path']
                data['commitWithin'] = 120000 # 2 minutes

                # calculate boost values
                boost_values = boost_script(data)
                conn.add(boost_values=boost_values, **data)

        conn.flush()
        logger.info('Updated batch %s' % i)

    logger.info('Starting optimize commit')
    conn.commit(optimize=True)
    logger.info('Finished optimize commit')
    conn.close()
