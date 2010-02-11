from zope.interface import Interface
from plone.indexer import indexer


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


# the `indexer` decorator needs to be applied manually here, since plone
# versions before 3.3 need to be able to access the bare indexing functions
physicalPathIndexer = indexer(Interface)(physicalPath)
physicalDepthIndexer = indexer(Interface)(physicalDepth)
parentPathsIndexer = indexer(Interface)(parentPaths)


def registerAttributes():
    try:
        from Products.CMFPlone.CatalogTool import registerIndexableAttribute
        registerIndexableAttribute('physicalPath', physicalPath)
        registerIndexableAttribute('physicalDepth', physicalDepth)
        registerIndexableAttribute('parentPaths', parentPaths)
    except ImportError:
        pass
