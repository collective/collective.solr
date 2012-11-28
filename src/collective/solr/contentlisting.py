from plone.app.contentlisting.interfaces import IContentListingObject
from plone.app.layout.icons.interfaces import IContentIcon
from plone.i18n.normalizer.interfaces import IIDNormalizer
from plone.uuid.interfaces import IUUID
from zope.component import getMultiAdapter, getUtility
from zope.globalrequest import getRequest
from zope.interface import implements


class FlareContentListingObject(object):
    implements(IContentListingObject)

    def __init__(self, flare):
        self.flare = flare

    def getId(self):
        return self.flare.getId

    def getObject(self):
        return self.flare.getObject()

    def getPath(self):
        return self.flare.getPath()

    def getURL(self):
        return self.flare.getURL()

    def uuid(self):
        if 'UID' in self.flare:
            return self.flare.UID
        else:
            return IUUID(self.getObject())

    def getIcon(self):
        return getMultiAdapter((self.getObject(), getRequest(), self.flare),
            interface=IContentIcon)()

    def getSize(self):
        self.flare.getObjSize

    def review_state(self):
        self.flare.review_state

    def listCreators(self):
        return self.flare.listCreators

    def Creator(self):
        return self.flare.Creator

    def Subject(self):
        return self.flare.Subject

    def Publisher(self):
        return NotImplementedError

    def listContributors(self):
        return NotImplementedError

    def Contributors(self):
        return self.listContributors()

    def Date(self, zone=None):
        return self.flare.Date

    def CreationDate(self, zone=None):
        return self.flare.created

    def EffectiveDate(self, zone=None):
        return self.flare.effective

    def ExpirationDate(self, zone=None):
        return self.flare.expires

    def ModificationDate(self, zone=None):
        return self.flare.modified

    def Format(self):
        raise NotImplementedError

    def Identifier(self):
        return self.getURL()

    def Language(self):
        self.Language

    def Rights(self):
        return NotImplementedError

    def Title(self):
        return self.flare.Title

    def Description(self):
        return self.flare.Description

    def Type(self):
        return self.flare.Type

    def ContentTypeClass(self):
        return "contenttype-" + getUtility(IIDNormalizer).normalize(self.PortalType())

    def PortalType(self):
        return self.flare.portal_type

    # Temporary to workaround a bug in current plone.app.search<=1.1.0
    def portal_type(self):
        return self.PortalType()

    def CroppedDescription(self):
        return self.flare.Description
