from rpc.kernel import Kernel
from uuid import uuid1
import builtins


_immutable_builtin_types = [
    bool, float, int, str, type(None)]
"""a list of immutable types built into JSON/msgpack"""


class Test:
    def some_method(self):
        return "aa"

    def another_method(self):
        import taxcalc
        return taxcalc.Records.cps_constructor().e00200.tolist()

    def failing_method(self):
        raise AssertionError("foo")


exported_vars = {
    "Test": Test,
    "builtins": builtins
}

imported_vars = {}


def wrap_result(r):
    res = {}
    cls = r.__class__
    if cls in _immutable_builtin_types:
        res['result'] = r
    else:
        oid = id(r)
        imported_vars[oid] = r
        res['otype'] = cls.__name__
        res['oid'] = oid
    return res


def handle_deref(oid):
    return {'result': imported_vars[oid]}


def handle_del(oid):
    del imported_vars[oid]


def handle_get_remote(varname):
    return wrap_result(exported_vars[varname])


def handle_getattr(oid, attrname):
    return wrap_result(getattr(imported_vars[oid], attrname))


def handle_call(oid, valargs, valkwargs, refargs, refkwargs):
    args = [imported_vars[arg_oid] for arg_oid in refargs] + valargs
    kwargs = {**{kw: imported_vars[arg_oid]
                 for kw, arg_oid in refkwargs.items()},
              **refkwargs}
    return wrap_result(imported_vars[oid](*args, **kwargs))


kernel = Kernel(serializer='msgpack')
kernel.register_handlers({'handle_deref': handle_deref,
                          'handle_del': handle_del,
                          'handle_get_remote': handle_get_remote,
                          'handle_getattr': handle_getattr,
                          'handle_call': handle_call})
kernel.run()
