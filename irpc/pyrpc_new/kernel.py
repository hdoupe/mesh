from rpc.kernel import Kernel
from client import _immutable_builtin_types
from uuid import uuid1


class Test:
    def some_method(self):
        return "aa"


exported_vars = {
    "Test": Test
}


myvars = {}


def wrap_result(r):
    res = {}
    cls = r.__class__
    if cls in _immutable_builtin_types:
        res['result'] = r
    else:
        oid = str(uuid1())
        myvars[oid] = r
        res['otype'] = cls.__name__
        res['oid'] = oid
    return res


def handle_get_remote(varname):
    return wrap_result(exported_vars[varname])


def handle_getattr(oid, attrname):
    return wrap_result(getattr(myvars[oid], attrname))


def handle_call(oid, callargs, callkwargs):
    return wrap_result(myvars[oid](*callargs, **callkwargs))


kernel = Kernel(serializer='msgpack')
kernel.register_handlers({'handle_get_remote': handle_get_remote,
                          'handle_getattr': handle_getattr,
                          'handle_call': handle_call})
kernel.run()
