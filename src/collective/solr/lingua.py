try:
    from Products.LinguaPlone.catalog import languageFilter

    languageFilter  # keep pyflakes happy
except ImportError:

    def languageFilter(args):
        pass
