# import `iterparse` from one of the various elementtree implementations,
# sorted according to response parsing benchmark results (on python 2.6):
#
#   xml.etree.ElementTree:  153 seconds
#   xml.etree.cElementTree:  72 seconds
#   ElementTree:            153 seconds
#   cElementTree:            72 seconds
#
# interestingly, on python 2.4 these are:
#   ElementTree:            124 seconds
#   cElementTree:            49 seconds

try:
    from xml.etree.cElementTree import iterparse
    iterparse       # make pyflakes happy
    source = 'xml.etree.cElementTree'
except ImportError:
    try:
        from cElementTree import iterparse
        iterparse       # make pyflakes happy
        source = 'cElementTree'
    except ImportError:
        try:
            from xml.etree.ElementTree import iterparse
            iterparse       # make pyflakes happy
            source = 'xml.etree.ElementTree'
        except ImportError:
            from elementtree.ElementTree import iterparse
            iterparse       # make pyflakes happy
            source = 'elementtree.ElementTree'
