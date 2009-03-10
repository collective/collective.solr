from zope.interface import implements
from elementtree.ElementTree import iterparse
from StringIO import StringIO
from DateTime import DateTime

from collective.solr.interfaces import ISolrFlare


class SolrFlare(object):
    """ a sol(a)r brain, i.e. a data container for search results """
    implements(ISolrFlare)

    __allow_access_to_unprotected_subobjects__ = True


class SolrResults(list):
    """ a list of results returned from solr, i.e. sol(a)r flares """


# unmarshallers for basic types
unmarshallers = {
    'null': lambda x: None,
    'int': int,
    'float': float,
    'double': float,
    'long': long,
    'bool': lambda x: x == 'true',
    'str': lambda x: x or '',
    'date': DateTime,
}

# nesting tags along with their factories
nested = {
    'arr': list,
    'lst': dict,
    'result': SolrResults,
    'doc': SolrFlare,
}

def setter(item, name, value):
    """ sets the named value on item respecting its type """
    if isinstance(item, list):
        item.append(value)      # name is ignored for lists
    elif isinstance(item, dict):
        item[name] = value
    else:                       # object is assumed...
        setattr(item, name, value)


class SolrResponse(object):
    """ a solr search response; TODO: this should get an interface!! """

    def __init__(self, data=None):
        if data is not None:
            self.parse(data)

    def parse(self, data):
        """ parse a solr response contained in a string or file-like object """
        if isinstance(data, basestring):
            data = StringIO(data)
        stack = [self]      # the response object is the outmost container
        elements = iterparse(data, events=('start', 'end'))
        for action, elem in elements:
            tag = elem.tag
            if action == 'start':
                if nested.has_key(tag):
                    data = nested[tag]()
                    for key, value in elem.attrib.items():
                        if not key == 'name':   # set extra attributes
                            setattr(data, key, value)
                    stack.append(data)
            elif action == 'end':
                if nested.has_key(tag):
                    data = stack.pop()
                    setter(stack[-1], elem.get('name'), data)
                elif unmarshallers.has_key(tag):
                    data = unmarshallers[tag](elem.text)
                    setter(stack[-1], elem.get('name'), data)
        return self

    def results(self):
        """ return only the list of results, i.e. a `SolrResults` instance """
        return getattr(self, 'response', [])

    def __len__(self):
        return len(self.results())

    def __getitem__(self, index):
        return self.results()[index]


class AttrDict(dict):
    """ a dictionary with attribute access """

    # look up attributes in dict
    def __getattr__(self, name):
        marker = []
        value = self.get(name, marker) 
        if value is not marker:
            return value
        else:
            raise AttributeError, name


class SolrField(AttrDict):
    """ a schema field representation """

    def __init__(self, *args, **kw):
        self['required'] = False
        self['multiValued'] = False
        super(SolrField, self).__init__(*args, **kw)


class SolrSchema(AttrDict):
    """ a solr schema parser:  the xml schema is partially parsed and the
        information collected is later on used both for indexing items as
        well as buiding search queries;  for the time being we are only
        interested in explicitly defined fields and their data types, so
        all <analyzer> (tokenizers, filters) and <dynamicField> information
        is ignored;  all the other fields like <uniqueKey>, <copyField>,
        <solrQueryParser>, <defaultSearchField> etc get ignored as well,
        since they are only used by solr, but not relevant when building
        search or indexing queries """

    def __init__(self, data=None):
        if data is not None:
            self.parse(data)

    def parse(self, data):
        """ parse a solr schema to collect information for building
            search and indexing queries later on """
        if isinstance(data, basestring):
            data = StringIO(data)
        self['requiredFields'] = required = []
        types = {}
        for action, elem in iterparse(data):
            name = elem.get('name')
            if elem.tag == 'fieldType':
                types[name] = elem.attrib
            elif elem.tag == 'field':
                field = SolrField(types[elem.get('type')])
                field.update(elem.attrib)
                field['class_'] = field['class']    # `.class` will not work
                for key, value in field.items():    # convert to `bool`s
                    if value in ('true', 'false'):
                        field[key] = value == 'true'
                self[name] = field
                if field.get('required', False):
                    required.append(name)
            elif elem.tag in ('uniqueKey', 'defaultSearchField'):
                self[elem.tag] = elem.text

