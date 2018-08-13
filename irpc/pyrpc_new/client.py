from rpc.client import Client


_local_netref_attrs = frozenset([
    '____cli__', '____oid__', '____otype__', '__class__', '__cmp__',
    '__del__', '__delattr__', '__dir__', '__doc__', '__getattr__',
    '__getattribute__', '__methods__', '__init__', '__metaclass__',
    '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
    '__setattr__', '__slots__', '__str__', '__weakref__', '__dict__',
    '__members__',  '__exit__', '__hash__', '__call__'
])
"""the set of attributes that are local to the netref object"""


_immutable_builtin_types = [
    bool, float, int, str, type(None)]
"""a list of immutable types built into JSON/msgpack"""

classes_cache = []


def syncreq(client, endpoint, *args, **kwargs):
    if isinstance(client, BaseNetref):
        client = client.____cli__
    j = client.submit(endpoint, args=args, kwargs=kwargs)
    r = client.get(j)
    print(j['result'])
    return j['result']


class BaseNetref(object):
    """The base netref class, from which all netref classes derive."""
    def __init__(self, client, oid, otype):
        self.____cli__ = client
        self.____oid__ = oid
        self.____otype__ = otype

    def __getattribute__(self, name):
        # Could implement __class__ manipulation later
        def go_get():
            return unwrap_result(
                self.____cli__,
                syncreq(self, 'handle_getattr',
                        oid=self.____oid__, attrname=name))
        if name in _local_netref_attrs:
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                return go_get()
        else:
            return go_get()

    def __call__(self, *args, **kwargs):
        return unwrap_result(
            self.____cli__,
            syncreq(self, 'handle_call',
                    oid=self.____oid__, callargs=args, callkwargs=kwargs))

    # To implement:
    # - __del__
    # - __delattr__
    # - __setattr__
    # - __dir__
    # - __hash__
    # - __cmp__
    # - __repr__
    # - __str__
    # - __exit__


class GenericNetref(BaseNetref):
    """
    We could have specialized netref classes in the future; this one is not.
    """
    pass


def unwrap_result(client, r):
    if 'result' in r:
        return r['result']
    else:
        return GenericNetref(client, r['oid'], r['otype'])


def get_remote(client, varname):
    return unwrap_result(client, syncreq(client, 'handle_get_remote', varname))


if __name__ == '__main__':
    with Client(serializer='msgpack') as cli:
        a = get_remote(cli, 'Test')
        b = a()
        print("Got " + b.some_method())
