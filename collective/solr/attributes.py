from Products.CMFPlone.CatalogTool import registerIndexableAttribute


def physicalPath(obj, **kwargs):
    """ return physical path as a string """
    return '/'.join(obj.getPhysicalPath())


def physicalDepth(obj, **kwargs):
    """ return depth of physical path """
    return len(obj.getPhysicalPath())


def parentPaths(obj, **kwargs):
    """ return all parent paths leading up to the object """
    elements = obj.getPhysicalPath()
    return ['/'.join(elements[:n+1]) for n in xrange(1, len(elements))]


def registerAttributes():
    registerIndexableAttribute('physicalPath', physicalPath)
    registerIndexableAttribute('physicalDepth', physicalDepth)
    registerIndexableAttribute('parentPaths', parentPaths)
