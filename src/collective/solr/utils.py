from re import UNICODE, compile

import six
from Acquisition import aq_base
from collective.solr.interfaces import ISolrSchema
from plone.registry.interfaces import IRegistry
from six.moves import range
from unidecode import unidecode
from zope.component import getUtility

if hasattr(str, "maketrans"):
    maketrans = str.maketrans
else:
    from string import maketrans


def getConfig():
    registry = getUtility(IRegistry)
    return registry.forInterface(ISolrSchema, prefix="collective.solr")


def isActive():
    """indicate if the solr connection should/can be used"""
    try:
        registry = getUtility(IRegistry)
        active = registry["collective.solr.active"]
    except KeyError:
        return False
    return active


def activate(active=True):
    """(de)activate the solr integration"""
    registry = getUtility(IRegistry)
    registry["collective.solr.active"] = active


def setupTranslationMap():
    """prepare translation map to remove all control characters except
    tab, new-line and carriage-return"""
    ctrls = trans = ""
    for n in range(0, 32):
        char = six.unichr(n)
        ctrls += char
        if char in "\t\n\r":
            trans += char
        else:
            trans += " "
    return maketrans(ctrls, trans)


translation_map = setupTranslationMap()


def prepareData(data):
    """modify data according to solr specifics, i.e. replace ':' by '$'
    for "allowedRolesAndUsers" etc;  please note that this function
    is also used while indexing, so no query-specific modification
    should happen here!"""
    allowed = data.get("allowedRolesAndUsers", None)
    if allowed is not None:
        data["allowedRolesAndUsers"] = [r.replace(":", "$") for r in allowed]
    language = data.get("Language", None)
    if language is not None:
        if language == "":
            data["Language"] = "any"
        elif isinstance(language, (tuple, list)) and "" in language:
            data["Language"] = [lang or "any" for lang in language]
    searchable = data.get("SearchableText", None)
    if searchable is not None:
        if isinstance(searchable, dict):
            searchable = searchable["query"]

        if isinstance(searchable, six.binary_type):
            searchable = searchable.decode("utf-8")
        if six.PY2:
            searchable = searchable.encode("utf-8")

        data["SearchableText"] = searchable.translate(translation_map)
        if isinstance(data["SearchableText"], six.binary_type):
            data["SearchableText"] = data["SearchableText"].decode("utf-8")
    # mangle path query from plone.app.collection
    path = data.get("path")
    if isinstance(path, dict) and not path.get("query"):
        data.pop("path")
    if "getObjPositionInParent" in data and data["getObjPositionInParent"] is None:
        data.pop("getObjPositionInParent")


simpleTerm = compile(r"^[\w\d]+$", UNICODE)


def isSimpleTerm(term):
    if isinstance(term, six.binary_type):
        term = six.text_type(term, "utf-8", "ignore")
    term = term.strip()
    return bool(simpleTerm.match(term))


reserved = compile(r"(AND|OR|NOT|[+\-&|!(){}\[\]^~*?:\\/]+)", UNICODE)
notSimpleCharacters = compile(r"[^\w\d\?\*\s]+", UNICODE)


def removeSpecialCharactersAndOperators(term):
    """
    Remove all special operators and characters used by Solr'
    Standard Query Parser (lucene)
    """
    return notSimpleCharacters.sub(" ", reserved.sub(" ", term))


operators = compile(r"(.*)\s+(AND|OR|NOT)\s+", UNICODE)
simpleCharacters = compile(r"^[\w\d\?\*\s]+$", UNICODE)


def isSimpleSearch(term):
    term = term.strip()
    if isinstance(term, six.binary_type):
        term = six.text_type(term, "utf-8", "ignore")
    if not term:
        return False
    num_quotes = term.count('"')
    if num_quotes % 2 == 1:
        return False
    if num_quotes > 1:
        # replace the quoted parts of the query with a marker
        parts = term.split('"')
        # take only the even parts (i.e. those outside the quotes)
        new_parts = []
        for i in range(0, len(parts)):
            if i % 2 == 0:
                new_parts.append(parts[i])
            else:
                new_parts.append("quoted")
        term = u"".join(new_parts)
    if bool(operators.match(term)):
        return False
    if bool(simpleCharacters.match(term)):
        return True
    term = term.strip()
    if not term:
        return True
    return False


def splitSimpleSearch(term):
    """Split a simple search term into tokens (words and phrases)"""
    if not isSimpleSearch(term):
        raise AssertionError("term is not a simple search")
    parts = term.split('"')
    tokens = []
    for i in range(0, len(parts)):
        if i % 2 == 0:
            # unquoted text
            words = [word for word in parts[i].split() if word]
            tokens.extend(words)
        else:
            # The uneven parts are those inside quotes.
            if parts[i]:
                tokens.append('"%s"' % parts[i])
    return tokens


wildCard = compile(r"^[\w\d\s*?]*[*?]+[\w\d\s*?]*$", UNICODE)


def isWildCard(term):
    if isinstance(term, six.binary_type):
        term = six.text_type(term, "utf-8", "ignore")
    return bool(wildCard.match(term))


def prepare_wildcard(value):
    # wildcards prevent Solr's field analyzer to run. So we need to replicate
    # all logic that's usually done in the text field.
    # Unfortunately we cannot easily inspect the field analyzer and tokenizer,
    # so we assume the default config contains ICUFoldingFilterFactory and hope
    # unidecode will produce the same results
    if not isinstance(value, six.text_type):
        value = six.text_type(value, "utf-8", "ignore")

    value = six.text_type(unidecode(value))

    # boolean operators must not be lowercased, otherwise Solr will interpret
    # them as search terms. So we split the search term into tokens and
    # lowercase only the non-operator parts.
    parts = []
    for item in value.split():
        parts.append(item.lower() if item not in ("AND", "OR", "NOT") else item)
    return " ".join(parts)


def findObjects(origin):
    """generator to recursively find and yield all zope objects below
    the given start point"""
    traverse = origin.unrestrictedTraverse
    base = "/".join(origin.getPhysicalPath())
    cut = len(base) + 1
    paths = [base]
    for idx, path in enumerate(paths):
        obj = traverse(path)
        yield path[cut:], obj
        if hasattr(aq_base(obj), "objectIds"):
            for id in obj.objectIds():
                paths.insert(idx + 1, path + "/" + id)


def padResults(results, start=0, **kw):
    if start:
        results[0:0] = [None] * start
    found = int(results.numFound)
    tail = found - len(results)
    results.extend([None] * tail)
