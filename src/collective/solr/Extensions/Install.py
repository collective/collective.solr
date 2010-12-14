#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (C) 2010, Mathieu PASQUET <mpa@makina-corpus.com>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
# 3. Neither the name of the <ORGANIZATION> nor the names of its
#    contributors may be used to endorse or promote products derived from
#    this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

__docformat__ = 'restructuredtext en'

import logging

from plone.browserlayer.utils import unregister_layer
from Products.CMFCore.utils import getToolByName

from collective.solr.interfaces import ISolrConnectionConfig 
from collective.solr.interfaces import ISolrConnectionManager
from collective.solr.interfaces import ISolrIndexQueueProcessor

def unregisterUtility(context, iface, name=None):
    sm = context.getSiteManager()
    if name:
        util = sm.queryUtility(iface, name=name)
    else:
        util = sm.getUtility(iface)
    if name:
        sm.unregisterUtility(util, iface, name=name)
    else:
        sm.unregisterUtility(provided=iface)
    if util:
        del util
    if not name:
        sm.utilities.unsubscribe((), iface)
    if iface in sm.utilities.__dict__['_provided']:
        del sm.utilities.__dict__['_provided'][iface]
    if iface in sm.utilities._subscribers[0]:
        del sm.utilities._subscribers[0][iface]

def uninstall(portal):
    logger = logging.getLogger('collective.solr.Uninstall')
    setup_tool = getToolByName(portal, 'portal_setup')
    setup_tool.runAllImportStepsFromProfile('profile-collective.solr:uninstall')
    cp = getToolByName(portal, 'portal_controlpanel')
    cp.unregisterConfiglet('SolrSettings')
    for iface, name in ((ISolrConnectionConfig, None),
                        (ISolrConnectionManager, None),
                        (ISolrIndexQueueProcessor, 'solr')):
        try:
            unregisterUtility(portal, iface, name)
        except:
            logger.debug('Cant unregister: %s/%s' % (iface, name))
    sm = portal.getSiteManager()
    try:
        unregister_layer('collective.solr', site_manager=sm)
    except KeyError:
        logger.debug('Browser layer not registered')

