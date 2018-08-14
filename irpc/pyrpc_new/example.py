from rpc.client import Client
from rpc.kernelmanager import KernelManager
from client import get_remote, deref
import itertools

kernel_info = {'new': {'module_path': 'kernel.py'}}

with KernelManager(kernel_info) as km:
    with Client(kernel_id='new', serializer='msgpack') as cli:
        a = get_remote(cli, 'Test')
        b = a()
        print("Got " + b.some_method())
        r = b.another_method()
        print("Got ", r)
        # Get remote builtins module
        rb = get_remote(cli, 'builtins')
        print("Got ", )
        # Get 1000 elements one-by-one. Doesn't take as long as the whole list
        list(itertools.islice(r, 1000))
        # Get all elements as serialized list
        wholelist = deref(r)
        # Reverse the list remotely, then retrieve it
        revlist = deref(rb.list(rb.reversed(r)))
        assert list(reversed(wholelist)) == revlist
