import pkg_resources

IS_PLONE4 = pkg_resources.get_distribution("Products.CMFPlone").version.startswith("4.")
