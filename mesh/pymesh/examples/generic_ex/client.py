from mesh.client import TaskFailure
from mesh.kernelmanager import KernelManager
from mesh.proxy.client import ProxyClient, deref
import itertools

kernel_info = {'new': {'module_path': 'kernel.py'}}

with KernelManager(kernel_info) as km:
    with ProxyClient(kernel_id='new', serializer='msgpack') as cli:
        a = cli.get_remote('Test')
        b = a()
        print("Got " + b.some_method())
        r = b.another_method()
        print("Got ", r)
        # Get remote builtins module
        rb = cli.get_remote('builtins')
        print("Got ", )
        # Get 1000 elements one-by-one. Doesn't take as long as the whole list
        list(itertools.islice(r, 1000))
        # Get all elements as serialized list
        wholelist = deref(r)
        # Reverse the list remotely, then retrieve it
        revlist = deref(rb.list(rb.reversed(r)))
        assert list(reversed(wholelist)) == revlist
        try:
            b.failing_method()
        except TaskFailure as e:
            assert e.args == ('AssertionError', 'foo')
        else:
            raise
