try:
    from xml.etree.cElementTree import iterparse; iterparse
except ImportError:
    try:
        from xml.etree.ElementTree import iterparse; iterparse
    except ImportError:
        try:
            from cElementTree import iterparse; iterparse
        except ImportError:
            from elementtree.ElementTree import iterparse; iterparse
