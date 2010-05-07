try:
    from xml.etree.cElementTree import iterparse; iterparse
    source = 'xml.etree.cElementTree'
except ImportError:
    try:
        from xml.etree.ElementTree import iterparse; iterparse
        source = 'xml.etree.ElementTree'
    except ImportError:
        try:
            from cElementTree import iterparse; iterparse
            source = 'cElementTree'
        except ImportError:
            from elementtree.ElementTree import iterparse; iterparse
            source = 'elementtree.ElementTree'
