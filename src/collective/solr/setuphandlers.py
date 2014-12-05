# -*- coding: utf-8 -*-
from Products.CMFCore.utils import getToolByName
import logging
logger = logging.getLogger('collective.solr')

PROFILE_ID = 'profile-collective.solr:default'


def migrateTo2(context):
    setup_tool = getToolByName(context, 'portal_setup')
    setup_tool.runImportStepFromProfile(PROFILE_ID, 'browserlayer')
    logger.info('Migrated to version 2: add browserlayer')
