from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware as CatalogMultiplex
from Products.CMFCore.utils import getToolByName
from Products.CMFDefault.permissions import ModifyPortalContent


def reorderedEvent(event):
    parent = event.object
    mtool = getToolByName(parent, "portal_membership")
    if mtool.checkPermission(ModifyPortalContent, parent):
        for child in parent.objectValues():
            if isinstance(child, CatalogMultiplex) or isinstance(
                child, CMFCatalogAware
            ):
                child.reindexObject(["getObjPositionInParent"])
