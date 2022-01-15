from datetime import datetime

from DateTime import DateTime

try:
    from ZTUtils.Lazy import Lazy, _marker
except ImportError:
    from Products.ZCatalog.Lazy import Lazy
    from Products.ZCatalog.Lazy import _marker

from xml.etree.cElementTree import iterparse

import six
from collective.solr.interfaces import ISolrFlare
from zope.interface import implementer


class AttrDict(dict):
    """a dictionary with attribute access"""

    def __getattr__(self, name):
        """look up attributes in dict"""
        marker = []
        value = self.get(name, marker)
        if value is not marker:
            return value
        else:
            raise AttributeError(name)


@implementer(ISolrFlare)
class SolrFlare(AttrDict):
    """a sol(a)r brain, i.e. a data container for search results"""

    __allow_access_to_unprotected_subobjects__ = True


class SolrResults(list):
    """a list of results returned from solr, i.e. sol(a)r flares"""


def parseDate(value):
    """use `DateTime` to parse a date, but take care of solr 1.4
    stripping away leading zeros for the year representation"""
    if value.find("-") < 4:
        year, rest = value.split("-", 1)
        value = "%04d-%s" % (int(year), rest)
    return DateTime(value)


def parse_date_as_datetime(value):
    if value.find("-") < 4:
        year, rest = value.split("-", 1)
        value = "%04d-%s" % (int(year), rest)
    format = "%Y-%m-%dT%H:%M:%S"
    if "." in value:
        format += ".%fZ"
    else:
        format += "Z"
    return datetime.strptime(value, format)


# unmarshallers for basic types
unmarshallers = {
    "null": lambda x: None,
    "int": int,
    "float": float,
    "double": float,
    "long": int,
    "bool": lambda x: x == "true",
    "str": lambda x: x or "",
    "date": parseDate,
}

# nesting tags along with their factories
nested = {"arr": list, "lst": dict, "result": SolrResults, "doc": SolrFlare}


def setter(item, name, value):
    """sets the named value on item respecting its type"""
    if isinstance(item, list):
        item.append(value)  # name is ignored for lists
    elif isinstance(item, dict):
        item[name] = value
    else:  # object is assumed...
        setattr(item, name, value)


class SolrResponse(Lazy):
    """a solr search response; TODO: this should get an interface!!"""

    __allow_access_to_unprotected_subobjects__ = True

    def __init__(self, data=None, unmarshallers=unmarshallers):
        self.unmarshallers = unmarshallers
        if data is not None:
            self.parse(data)

    def parse(self, data):
        """parse a solr response contained in a string or file-like object"""
        if isinstance(data, six.text_type):
            data = data.encode("utf-8")
        if isinstance(data, six.binary_type):
            data = six.BytesIO(data)
        stack = [self]  # the response object is the outmost container
        elements = iterparse(data, events=("start", "end"))
        for action, elem in elements:
            tag = elem.tag
            if action == "start":
                if tag in nested:
                    data = nested[tag]()
                    for key, value in elem.attrib.items():
                        if not key == "name":  # set extra attributes
                            if isinstance(key, six.binary_type):
                                key = key.decode("utf-8")
                            if isinstance(value, six.binary_type):
                                value = value.decode("utf-8")
                            setattr(data, key, value)
                    stack.append(data)
            elif action == "end":
                if tag in nested:
                    data = stack.pop()
                    setter(stack[-1], elem.get("name"), data)
                elif tag in self.unmarshallers:
                    data = self.unmarshallers[tag](elem.text)
                    setter(stack[-1], elem.get("name"), data)
        return self

    def results(self):
        """return only the list of results, i.e. a `SolrResults` instance"""
        return getattr(self, "response", [])

    @property
    def actual_result_count(self):
        """
        return the actual_result_count
        """
        if self._rlen is not _marker:
            return self._rlen
        if getattr(self, "response", None):
            return int(self.response.numFound)
        return 0

    @actual_result_count.setter
    def actual_result_count(self, value):
        self._rlen = value

    def __len__(self):
        if self._len is not _marker:
            return self._len
        self._len = len(self.results())
        return self._len

    def __getitem__(self, index):
        return self.results()[index]


class SolrField(AttrDict):
    """a schema field representation"""

    def __init__(self, *args, **kw):
        self["required"] = False
        self["multiValued"] = False
        super(SolrField, self).__init__(*args, **kw)


class AttrStr(str):
    """a string class with attributes"""

    def __new__(self, value, **kw):
        return str.__new__(self, value)

    def __init__(self, value, **kw):
        self.__dict__.update(kw)


class SolrSchema(AttrDict):
    """a solr schema parser:  the xml schema is partially parsed and the
    information collected is later on used both for indexing items as
    well as buiding search queries;  for the time being we are mostly
    interested in explicitly defined fields and their data types, so
    all <analyzer> (tokenizers, filters) and <dynamicField> information
    is ignored;  some of the other fields relevant to the implementation,
    like <uniqueKey>, <solrQueryParser> or <defaultSearchField>, are also
    parsed and provided, all others are ignored"""

    def __init__(self, data=None):
        if data is not None:
            self.parse(data)

    def parse(self, data):
        """parse a solr schema to collect information for building
        search and indexing queries later on"""
        if isinstance(data, six.string_types):
            data = six.StringIO(data)
        self["requiredFields"] = required = []
        types = {}
        for action, elem in iterparse(data):
            name = elem.get("name")
            if elem.tag == "fieldType":
                types[name] = elem.attrib
            elif elem.tag == "field":
                field = SolrField(types[elem.get("type")])
                field.update(elem.attrib)
                field["class_"] = field["class"]  # `.class` will not work
                for key, value in field.items():  # convert to `bool`s
                    if value in ("true", "false"):
                        field[key] = value == "true"
                self[name] = field
                if field.get("required", False):
                    required.append(name)
            elif elem.tag in ("uniqueKey", "defaultSearchField"):
                self[elem.tag] = elem.text
            elif elem.tag == "solrQueryParser":
                self[elem.tag] = AttrStr(elem.text, **elem.attrib)

    @property
    def fields(self):
        """return list of all fields the schema consists of"""
        for name, field in self.items():
            if isinstance(field, SolrField):
                yield field

    @property
    def stored(self):
        """return names of all stored fields, a.k.a. metadata"""
        for field in self.fields:
            if field.stored:
                yield field.name
