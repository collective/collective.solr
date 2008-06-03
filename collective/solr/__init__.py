# the existance of __init__.py make this a module...


# temporary fix for not having the formerly persistent utility cause trouble...

def _persistent_load(self, reference):
    if isinstance(reference, tuple):
        try:
            return self.load_persistent(*reference)
        except TypeError:
            return None
    elif isinstance(reference, str):
        return self.load_oid(reference)
    else:
        try:
            reference_type, args = reference
        except ValueError:
            # weakref
            return self.loaders['w'](self, *reference)
        else:
            return self.loaders[reference_type](self, *args)

from ZODB.serialize import ObjectReader
ObjectReader._persistent_load = _persistent_load

