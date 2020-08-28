# -*- coding: utf-8 -*-
from re import compile
import six

# Solr/lucene reserved characters/terms:
#   + - && || ! ( ) { } [ ] ^ " ~ * ? : \ /
#   (see http://wiki.apache.org/solr/SolrQuerySyntax)
# Four groups for tokenizer:
# 1) Whitespace (\s+)
# 2) Boolean operators, ampersand and pipe literals ([\&\|])
# 2) Any non reserved characters (normal text) ([^-(){}\[\]+!^\"~*?:\\/\s]+)
# 3) Any grouping characters ([(){}\[\]"])
# 4) Any special operators ([-+!^~*?:\\/])
query_tokenizer = compile(
    r"(?:(\s+)|"
    r"([\&\|])|"
    r"([^-(){}\[\]+!^\"~*?:\\/\&\|\s]+)|"
    r'([(){}\[\]"])|'
    r"([-+!^~*?:\\/]))"
)


class Whitespace(object):
    def __nonzero__(self):
        return False

    def __str__(self):
        return " "


class Group(list):
    def __init__(self, start=None, end=None):
        self.start = start
        self.end = end
        self.isgroup = False  # Set on pop

    def __str__(self):
        res = [x for x in self if x]
        lenres = len(res)
        if lenres == 0:
            return ""
        elif lenres == 1:
            return six.text_type(res[0])
        # Otherwise, also print whitespace
        return "%s%s%s" % (
            self.start,
            "".join([six.text_type(x) for x in self]),
            self.end,
        )


class Quote(Group):
    def __str__(self):
        if not self.end:
            # No finishing quote, we have to add new group if there is
            # whitespace
            if [x for x in self if isinstance(x, Whitespace)]:
                self.start = "(%s" % self.start
                self.end = ")"
        return "%s%s%s" % (
            self.start,
            "".join([six.text_type(x) for x in self]),
            self.end,
        )


class Range(Group):
    def __str__(self):
        first = last = "*"
        if len(self) == 0:
            return ""
        if "TO" not in self:
            # Not valid range, quote
            return "\\%s%s\\%s" % (
                self.start,
                "".join([six.text_type(x) for x in self]),
                self.end,
            )
        else:
            # split on 'TO'
            split = self.index("TO")
            if split > 0:
                first = "".join(
                    [
                        six.text_type(x)
                        for x in self[:split]
                        if not isinstance(x, Whitespace)
                    ]
                )
            if split < (len(self) - 1):
                last = "".join(
                    [
                        six.text_type(x)
                        for x in self[split + 1 :]
                        if not isinstance(x, Whitespace)
                    ]
                )
        return "%s%s TO %s%s" % (self.start, first, last, self.end)


class Stack(list):
    def __init__(self):
        self.append([])

    def add(self, item):
        self.current.append(item)
        self.append(item)

    @property
    def current(self):
        return self[-1]

    def __str__(self):
        return "".join([six.text_type(x) for x in self[0]])


def quote(term, textfield=False, prefix_wildcard=False):
    if isinstance(term, six.binary_type):
        term = term.decode("utf-8")
    stack = Stack()
    tokens = query_tokenizer.findall(term.strip())
    # Counter enables lookahead
    i = 0
    stop = len(tokens)
    while i < stop:
        whitespace, boolean, text, grouping, special = tokens[i]

        if whitespace:
            # Add whitespace if group text, range and group filter on display
            if isinstance(stack.current, Group):
                stack.current.append(Whitespace())
            elif isinstance(stack.current, list):
                # We have whitespace with no grouping, insert group
                new = Group("(", ")")
                new.extend(stack.current)
                new.append(Whitespace())
                stack.current[:] = []
                stack.add(new)

        elif boolean:
            # It's an operator if the following token is the same...
            if i < stop - 1 and boolean == tokens[i + 1][1]:
                # Add operator if we're inside a group
                if isinstance(stack.current, Group):
                    stack.current.append(boolean)
                elif isinstance(stack.current, list):
                    # We have an operator with no grouping, insert group
                    new = Group("(", ")")
                    new.extend(stack.current)
                    new.append(boolean)
                    stack.current[:] = []
                    stack.add(new)
            else:
                stack.current.append(boolean)

        elif grouping:
            # [] (inclusive range), {} (exclusive range), always with TO inside
            # () group
            # "" for quotes
            if grouping == '"':
                if isinstance(stack.current, Quote):
                    # Handle empty double quote
                    if not stack.current:
                        stack.current.end = '\\"'
                    else:
                        stack.current.start = stack.current.end = '"'
                        stack.current.isgroup = True
                    stack.pop()
                else:
                    # Right now this is just a single quote,
                    # we set proper start and end before popping
                    new = Quote(start='\\"', end="")
                    stack.add(new)
            elif isinstance(stack.current, Quote):
                # If we're in a quote, escape and print
                stack.current.append("\\%s" % grouping)
            elif grouping in "[{":
                new = Range(start=grouping, end={"[": "]", "{": "}"}[grouping])
                stack.add(new)
            elif grouping == "(":
                new = Group(start="(", end=")")
                stack.add(new)
            elif grouping in "]})":
                if isinstance(stack.current, Group) and stack.current.end == grouping:
                    stack.current.isgroup = True
                    stack.pop()
                else:
                    stack.current.append("\\%s" % grouping)

        elif text:
            stack.current.append(text)

        elif special:
            if special == "\\":
                # Inspect next to see if it's quoted special or quoted group
                if (i + 1) < stop:
                    _, _, _, g2, s2 = tokens[i + 1]
                    if s2:
                        stack.current.append("%s%s" % (special, s2))
                        # Jump ahead
                        i += 1
                    elif g2:
                        stack.current.append("%s%s" % (special, g2))
                        # Jump ahead
                        i += 1
                    else:
                        # Quote it
                        stack.current.append("\\%s" % special)
                else:
                    # Quote it
                    stack.current.append("\\\\")
            elif isinstance(stack.current, Quote):
                stack.current.append("\\%s" % special)
            elif special in "+-":
                if (i + 1) < stop:
                    _, _, t2, g2, _ = tokens[i + 1]
                    # We allow + and - in front of phrase and text
                    if t2 or g2 == '"':
                        if textfield and i > 0 and tokens[i - 1][2]:
                            # Quote intra-word hyphens, so they are normal text
                            # and not syntax
                            stack.current.append("\\%s" % special)
                        else:
                            stack.current.append(special)
                    else:
                        # Quote it
                        stack.current.append("\\%s" % special)
            elif special in "~^":
                # Fuzzy or proximity is always after a term or phrase, and
                # sometimes before int or float like roam~0.8 or
                # "jakarta apache"~10
                if i > 0:
                    _, _, t0, g0, _ = tokens[i - 1]
                    if t0 or g0 == '"':
                        # Look ahead to check for integer or float

                        if (i + 1) < stop:
                            _, _, t2, _, _ = tokens[i + 1]
                            try:  # float(t2) might fail
                                if t2 and float(t2):
                                    stack.current.append("%s%s" % (special, t2))
                                    # Jump ahead
                                    i += 1
                                else:
                                    stack.current.append(special)
                            except ValueError:
                                stack.current.append(special)
                        else:  # (i+1)<stop
                            stack.current.append(special)
                    else:  # t0 or g0 == '"'
                        stack.current.append("\\%s" % special)
                else:  # i>0
                    stack.current.append("\\%s" % special)
            elif special in "?*":
                # ? and * can not be the first characters of a search
                # if prefix_wildcard is not enabled
                if (
                    (
                        stack.current
                        and not getattr(stack.current[-1], "isgroup", False)
                        and (
                            isinstance(stack.current[-1], six.text_type)
                            and not stack.current[-1] in special
                        )
                    )
                    or (
                        prefix_wildcard
                        and (not stack.current or not stack.current[-1] in special)
                    )
                    or isinstance(stack.current, Range)
                ):
                    stack.current.append(special)
            elif special in "/":
                stack.current.append("\\%s" % special)
            elif isinstance(stack.current, Range):
                stack.current.append(special)
            elif isinstance(stack.current, Group):
                stack.current.append("\\%s" % special)
            elif isinstance(stack.current, list):
                stack.current.append("\\%s" % special)
        i += 1
    return six.text_type(stack)


def quote_iterable_item(term):
    if isinstance(term, (int, float)):
        return str(term)
    quoted = quote(term)
    if not quoted.startswith('"') and not quoted == term:
        quoted = quote('"' + term + '"')
    return quoted
