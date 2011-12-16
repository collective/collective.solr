from Acquisition import aq_base
from archetypes.schemaextender.field import ExtensionField
from archetypes.schemaextender.interfaces import ISchemaExtender
from plone.indexer import indexer
from Products.Archetypes.atapi import BooleanField
from Products.Archetypes.atapi import BooleanWidget
from Products.Archetypes.atapi import TextAreaWidget
from Products.Archetypes.atapi import TextField
from Products.Archetypes.interfaces import IBaseObject
from zope.interface import implements
from zope.interface import Interface

from collective.solr import SolrMessageFactory as _


@indexer(IBaseObject)
def searchwords(obj):
    field = obj.getField('searchwords')
    if field is None:
        raise AttributeError
    words = field.get(obj)
    words = [w.strip('\r ').decode('utf-8') for w in words.split('\n')]
    return tuple([w.lower() for w in words if w])


@indexer(Interface)
def showinsearch(obj):
    # if the object isn't an Archetype, it should be included
    getField = getattr(aq_base(obj), 'getField', None)
    if getField is None:
        return True
    # if the object doesn't have the field, it should be included
    field = obj.getField('showinsearch')
    if field is None:
        return True
    value = field.get(obj)
    # None is the default value, meaning no value has been set, we treat this
    # as 'should be included in search'
    if value is None:
        value = True
    return value


class ExtentionTextField(ExtensionField, TextField):
    pass


class ExtensionBooleanField(ExtensionField, BooleanField):
    pass


class SearchExtender(object):
    """Adapter that adds search metadata."""

    implements(ISchemaExtender)

    _fields = [
        ExtensionBooleanField(
            'showinsearch',
            languageIndependent=True,
            schemata='settings',
            default=True,
            widget=BooleanWidget(
                label=_(u"Show in search"),
                visible={"edit": "visible", "view": "invisible"},
                description="",
            )),

        ExtentionTextField(
            'searchwords',
            searchable=True,
            schemata='settings',
            languageIndependent=False,
            widget=TextAreaWidget(
                label=_(u"Search words"),
                description="Specify words for which this item will show up "
                    "as the first search result. Multiple words can be "
                    "specified on new lines.",
                visible={"edit": "visible", "view": "invisible"},
            )),
        ]

    def __init__(self, context):
        self.context = context

    def getFields(self):
        return self._fields
