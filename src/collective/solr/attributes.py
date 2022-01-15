from plone.indexer import indexer
from six.moves import range
from zope.interface import Interface


@indexer(Interface)
def path_string(obj, **kwargs):
    """return physical path as a string"""
    return "/".join(obj.getPhysicalPath())


@indexer(Interface)
def path_depth(obj, **kwargs):
    """return depth of physical path"""
    return len(obj.getPhysicalPath())


@indexer(Interface)
def path_parents(obj, **kwargs):
    """return all parent paths leading up to the object"""
    elements = obj.getPhysicalPath()
    return ["/".join(elements[: n + 1]) for n in range(1, len(elements))]
