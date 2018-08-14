from rpc.client import Client


_local_netref_attrs = frozenset([
    '____proxyclient__', '____oid__', '____otype__', '__class__', '__cmp__',
    '__del__', '__delattr__', '__dir__', '__doc__', '__getattr__',
    '__getattribute__', '__methods__', '__init__', '__metaclass__',
    '__module__', '__new__', '__reduce__', '__reduce_ex__', '__repr__',
    '__setattr__', '__slots__', '__str__', '__weakref__', '__dict__',
    '__members__',  '__exit__', '__hash__', '__call__', '____deref__',
    '____unwrapped_sync_req__'
])
"""the set of attributes that are local to the netref object"""


class ProxyClient:
    def __init__(self, *args, **kwargs):
        self.netrefs = {}
        # Allow reusing an existing client
        if 'client' in kwargs:
            self.client = kwargs['client']
            self._managed_client = False
        else:
            self.client = Client(*args, **kwargs)
            self._managed_client = True

    def sync_req(self, endpoint, *args, **kwargs):
        return self.client.do_task(endpoint, args, kwargs)

    def async_req(self, endpoint, *args, **kwargs):
        # TODO: Make this not wait for the result
        self.client.do_task(endpoint, args, kwargs)

    def unwrap_result(self, r):
        if 'result' in r:
            return r['result']
        elif r['oid'] in self.netrefs:
            return self.netrefs[r['oid']]
        else:
            ref = GenericNetref(self, r['oid'], r['otype'])
            self.netrefs[r['oid']] = ref
            return ref

    def unwrapped_sync_req(self, *args, **kwargs):
        return self.unwrap_result(self.sync_req(*args, **kwargs))

    def get_remote(self, varname):
        return self.unwrapped_sync_req('handle_get_remote', varname)

    def __enter__(self, *args, **kwargs):
        if self._managed_client:
            self.client.__enter__(*args, **kwargs)
            return self
        else:
            raise AttributeError('__enter__')

    def __exit__(self, *args, **kwargs):
        if self._managed_client:
            return self.client.__exit__(*args, **kwargs)
        else:
            raise AttributeError('__exit__')


class BaseNetref(object):
    """The base netref class, from which all netref classes derive."""
    def __init__(self, client, oid, otype):
        self.____proxyclient__ = client
        self.____oid__ = oid
        self.____otype__ = otype

    def ____unwrapped_sync_req__(self, endpoint, *args, **kwargs):
        return self.____proxyclient__.unwrapped_sync_req(
            endpoint, *args, **kwargs, oid=self.____oid__)

    def __getattribute__(self, name):
        # Could implement __class__ manipulation later
        def get_remote_attr():
            return self.____unwrapped_sync_req__(
                'handle_getattr', attrname=name)
        if name in _local_netref_attrs:
            try:
                return object.__getattribute__(self, name)
            except AttributeError:
                return get_remote_attr()
        else:
            return get_remote_attr()

    def __call__(self, *args, **kwargs):
        valargs, valkwargs, refargs, refkwargs = [], {}, [], {}
        for arg in args:
            if isinstance(arg, BaseNetref):
                refargs.append(arg.____oid__)
            else:
                valargs.append(arg)
        for kw, arg in kwargs.items():
            if isinstance(arg, BaseNetref):
                refkwargs[kw] = arg.____oid__
            else:
                valkwargs[kw] = arg
        return self.____unwrapped_sync_req__(
                    'handle_call',
                    valargs=valargs, valkwargs=valkwargs,
                    refargs=refargs, refkwargs=refkwargs)

    def __iter__(self):
        return self.__iter__()

    def __next__(self):
        return self.__next__()

    def __len__(self):
        return self.__len__()

    def ____deref__(self):
        return self.____unwrapped_sync_req__('handle_deref')

    def __del__(self):
        try:
            self.____proxyclient__.async_req('handle_del', oid=self.____oid__)
        except BaseException:
            pass

    # To implement:
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
    We could have specialized netref classes in the future; this one is not
    specialized.
    """
    pass


def deref(netref):
    return netref.____deref__()
