import argparse
import logging
import sys

import transaction
from collective.solr.browser.maintenance import SolrMaintenanceView
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.utils import activate
from Testing.makerequest import makerequest
from zope.component import queryUtility
from zope.site.hooks import setHooks, setSite

logger = logging.getLogger()


def _get_site(app, args):
    # Zope.Startup.zopectl.ZopeCmd.run_entrypoint promises to pass the entry
    # point's name as the first argument and any further arguments after that,
    # but that does not work with plone.recipe.zope2instance. Using positional
    # arguments therefore is unreliable - resolve to using a flag.
    parser = argparse.ArgumentParser()
    parser.add_argument("--plonesite", help="Name of the Plone site", default=None)
    namespace, unused = parser.parse_known_args(args)
    name = namespace.plonesite
    if name is not None:
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
    logger.info("Opened Solr connection to %s" % conn.host)
    return conn


def solr_activate(app, args):
    _get_site(app, args)
    activate(active=True)
    transaction.commit()


def solr_deactivate(app, args):
    _get_site(app, args)
    activate(active=False)
    transaction.commit()


def solr_clear_index(app, args):
    """Removes all data from a Solr index. Equivalent to removing the
    `data/index` directory while Solr is stopped.
    You can optionally specify the id of the Plone site with
    --plonesite <siteid>.
    """
    _get_site(app, args)  # calls setSite so queryUtility works
    conn = _solr_connection()
    conn.deleteByQuery("[* TO *]")
    conn.commit(optimize=True)
    conn.close()


def solr_reindex(app, args):
    """Reindex Solr. This is equivalent to /@@solr-maintenance/reindex, but
    can handle more documents. Using reindex from the browser will stop
    eventually if there are too many documents, leaving the index incomplete.
    You can optionally specify the id of the Plone site with
    --plonesite <siteid>.
    """
    site = makerequest(_get_site(app, args))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--ignore_exceptions",
        help="Ignore exceptions during reindexing (yes/no)",
        choices=["yes", "no"],
        default="yes",
    )
    namespace, unused = parser.parse_known_args(args)
    ignore_exceptions = namespace.ignore_exceptions == "yes"
    mv = SolrMaintenanceView(site, site.REQUEST)
    mv.reindex(ignore_exceptions=ignore_exceptions)


def solr_cleanup(app, args):
    """Cleanup Solr index. Remove no longer existing items from Solr index.
    This is equivalent to /@@solr-maintenance/cleanup.
    """
    site = makerequest(_get_site(app, args))
    parser = argparse.ArgumentParser()

    namespace, unused = parser.parse_known_args(args)
    mv = SolrMaintenanceView(site, site.REQUEST)
    mv.cleanup()


def solr_sync(app, args):
    """Sync Solr index.
    Index missing objects and remove no longer existing objects from Solr.
    This is equivalent to /@@solr-maintenance/sync.
    """
    site = makerequest(_get_site(app, args))
    parser = argparse.ArgumentParser()

    namespace, unused = parser.parse_known_args(args)
    mv = SolrMaintenanceView(site, site.REQUEST)
    mv.sync()
