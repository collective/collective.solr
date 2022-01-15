import logging

from collective.solr.interfaces import ISolrConnectionConfig, ISolrSchema
from plone import api
from plone.registry import Record, field
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getSiteManager, getUtility, queryUtility

logger = logging.getLogger("collective.solr")
PROFILE_ID = "profile-collective.solr:default"


def migrateTo2(context):
    setup_tool = getToolByName(context, "portal_setup")
    setup_tool.runImportStepFromProfile(PROFILE_ID, "browserlayer")
    logger.info("Migrated to version 2: add browserlayer")


def update_registry(context):
    registry = getUtility(IRegistry)
    util = queryUtility(ISolrConnectionConfig)
    if util is not None:
        # Preferably we would get the previous data from this utility, so we
        # can restore the settings.  But the utility is broken.  The best we
        # can do, is remove it.
        sm = getSiteManager()
        sm.unregisterUtility(provided=ISolrConnectionConfig)

    registry.registerInterface(ISolrSchema, prefix="collective.solr")


def migrateTo4(context):
    registry = getUtility(IRegistry)
    if "collective.solr.async" in registry.records:
        old_record = registry.records["collective.solr.async"]
        registry.records["collective.solr.async_indexing"] = old_record
        del registry.records["collective.solr.async"]
        logger.info("Migrated to async_indexing setting")

    pt = api.portal.get_tool("portal_types")
    type_ids = (
        "Collection",
        "Document",
        "Event",
        "File",
        "Folder",
        "Image",
        "Link",
        "News Item",
    )
    new_behavior = "collective.solr.behaviors.ISolrFields"
    for type_id in type_ids:
        if type_id not in pt.objectIds():
            continue
        fti = pt[type_id]
        if new_behavior not in fti.behaviors:
            fti.behaviors += (new_behavior,)
            logger.info("Added new behavior to {}".format(type_id))

    logger.info("Migrated to version 4")


def migrate_to_5(context):
    registry = getUtility(IRegistry)
    if "collective.solr.login" not in registry.records:
        registry_field = field.TextLine(title=u"Login")
        registry_record = Record(registry_field)
        registry_record.value = None
        registry.records["collective.solr.login"] = registry_record
        logger.info("Create registry entry for collective.solr.login")
    if "collective.solr.password" not in registry.records:
        registry_field = field.TextLine(title=u"Password")
        registry_record = Record(registry_field)
        registry_record.value = None
        registry.records["collective.solr.password"] = registry_record
        logger.info("Create registry entry for collective.solr.password")
    if "collective.solr.use_tika" not in registry.records:
        registry_field = field.Bool(title=u"Use Tika")
        registry_record = Record(registry_field)
        registry_record.value = False
        registry.records["collective.solr.use_tika"] = registry_record
        logger.info("Create registry entry for collective.solr.use_tika")
    logger.info("Migrated to version 5")


def migrate_to_6(context):
    registry = getUtility(IRegistry)
    old_login = None
    old_password = None

    if "collective.solr.login" in registry.records:
        old_login = registry["collective.solr.login"]
        del registry.records["collective.solr.login"]
        logger.info("Remove registry entry for collective.solr.login")
    if "collective.solr.password" in registry.records:
        old_password = registry["collective.solr.password"]
        del registry.records["collective.solr.password"]
        logger.info("Remove registry entry for collective.solr.password")

    if "collective.solr.solr_login" not in registry.records:
        registry_field = field.TextLine(title=u"Login")
        registry_record = Record(registry_field)
        if old_login:
            registry_record.value = old_login
        else:
            registry_record.value = None
        registry.records["collective.solr.solr_login"] = registry_record
        logger.info("Create registry entry for collective.solr.solr_login")
    if "collective.solr_password" not in registry.records:
        registry_field = field.TextLine(title=u"Password")
        registry_record = Record(registry_field)
        if old_password:
            registry_record.value = old_password
        else:
            registry_record.value = None
        registry.records["collective.solr.solr_password"] = registry_record
        logger.info("Create registry entry for collective.solr.solr_password")

    logger.info("Migrated to version 6")


def migrate_to_7(context):
    registry = getUtility(IRegistry)
    if "collective.solr.tika_default_field" not in registry.records:
        registry_field = field.TextLine(title=u"Tika Default Field")
        registry_record = Record(registry_field)
        registry_record.value = "content"
        registry.records["collective.solr.tika_default_field"] = registry_record
    logger.info("Migrated to version 7")
