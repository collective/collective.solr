# -*- coding: utf-8 -*-


def uninstall(portal, reinstall=False):
    if not reinstall:
        setup_tool = portal.portal_setup
        profile = 'profile-collective.solr:uninstall'
        setup_tool.runAllImportStepsFromProfile(profile)
