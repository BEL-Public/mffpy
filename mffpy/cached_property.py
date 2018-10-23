
def cached_property(fn):
    cached_prop = '_cached_'+fn.__name__
    @property
    def _cached_property(self):
        try:
            return getattr(self, cached_prop)
        except AttributeError:
            ans = fn(self)
            setattr(self, cached_prop, ans)
            return ans
    return _cached_property
