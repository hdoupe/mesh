from rpc.kernel import Kernel
import builtins


_immutable_builtin_types = [
    bool, float, int, str, type(None)]
"""a list of immutable types built into JSON/msgpack"""


class ProxyKernel(Kernel):
    def __init__(self, exported_vars={}, serializer='msgpack',
                 **kwargs):
        super().__init__(serializer=serializer, **kwargs)
        self.exported_vars = {'builtins': builtins, **exported_vars}
        self.imported_vars = {}
        self.register_handlers({'handle_deref': self.handle_deref,
                                'handle_del': self.handle_del,
                                'handle_get_remote': self.handle_get_remote,
                                'handle_getattr': self.handle_getattr,
                                'handle_call': self.handle_call,
                                'handle_setattr': self.handle_setattr})

    def wrap_result(self, r):
        res = {}
        cls = r.__class__
        if cls in _immutable_builtin_types:
            res['result'] = r
        else:
            oid = id(r)
            self.imported_vars[oid] = r
            res['otype'] = cls.__name__
            res['oid'] = oid
        return res

    def handle_deref(self, oid):
        return {'result': self.imported_vars[oid]}

    def handle_del(self, oid):
        del self.imported_vars[oid]

    def handle_get_remote(self, varname):
        return self.wrap_result(self.exported_vars[varname])

    def handle_getattr(self, oid, attrname):
        return self.wrap_result(getattr(self.imported_vars[oid], attrname))

    def handle_setattr(self, oid, attrname, attrval=None, attrref=None):
        if attrref:
            setattr(self.imported_vars[oid], attrname,
                    self.imported_vars[attrref])
        else:
            setattr(self.imported_vars[oid], attrname, attrval)

    def handle_call(self, oid, valargs, valkwargs, refargs, refkwargs):
        args = [self.imported_vars[arg_oid] for arg_oid in refargs] + valargs
        kwargs = {**{kw: self.imported_vars[arg_oid]
                     for kw, arg_oid in refkwargs.items()},
                  **valkwargs}
        return self.wrap_result(self.imported_vars[oid](*args, **kwargs))
