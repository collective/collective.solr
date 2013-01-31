def reorderedEvent(obj, event):
    mtool = getToolByName(obj, 'portal_membership')
    if mtool.checkPermission(ModifyPortalCOntent, parent):
        for child in obj.objectValues():
            if isinstance(child, CatalogMultiPlex) or isinstance(child, CMFCatalogAware):
                child.reindexchildect(['getchildPositionInParent'])
