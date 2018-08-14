# Cross-Platform Protocol/Glue/Remote-Procedure-Call

`irpc` facilitates cross platform development. Currently, this project is experimental, and we are actively working to improve its functionality and optimize its architecture. `irpc` should be easy to use, understand, modify, and extend. This project has been developed with two problems in mind:

- how to easily integrate a library written in Fortran with a library written in Python
- how to easily integrate Python libraries that are likely to have incompatible dependency requirements

We want to solve this problems in such a way that users need no knowledge of messaging queues, serialization techniques, or remote-procedure-protocols.

Approach
---------

`irpc` follows a client/kernel model where the client and kernel define a set of endpoints through which the user submits data through the client to the kernel and the kernel responds with the results from the function corresponding to that endpoint. Lucas has extended this approach by implementing a class proxy protocol on top of it which allows for the sequential management of state on the kernel side.

"kernel" is defined as a process that executes code upon request. A "client" facilitates the interaction between the user who is in one environment (and process) and a "kernel" which is in a different process and potentially different environment.

The client and kernel do not need to be in the same language or computing environment. So far, this project has successfully integrated Python and Fortran libraries as well as Python libraries in different conda environments. The upside of this approach is that you could simultaneously run kernels in R, C, Fortran (with C-bindings), and Python. The user could spin up a client for each kernel and submit data to them. The kernels could even spin up clients to communicate with kernels written in other languages. Note that the same kernel can accept data from clients in multiple languages. That is, special kernels for the Python-to-R interaction and another for the Python-to-Fortran interaction are not needed. Only a Python kernel with the correct endpoints is needed.

API
----

I reference the Python API for this project because it closer to our vision for a more stable API.

Key Objects:
- `Kernel` -- registers handlers and executes tasks corresponding to them
- `Client` -- submits tasks and arguments to kernel and returns result; handles data serialization and port registration
- `KernelManager` -- spins up `Kernel` instances in subprocesses

Key usage pattern:

```
from rpc.kernelmanager import KernelManager
from rpc.client import Client

kernel_info = {
    'taxcalc1': {
        module_path': 'taxcalc_kernel.py',
        'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-dev/bin/python'
    }
}

endpoint = 'taxcalc_endpoint'
args = (arg1, arg2, )
kwargs = {'kwarg1': v1, 'kwarg2': v2}


with KernelManager(kernel_info) as km:
    client = Client(kernel_id='taxcalc1')
    task = client.submit(endpoint, args=args, kwargs=kwargs)
    result = client.get(task)
    print(result)

```

The `taxcalc_kernel.py` module:

```
def taxcalc_endpoint(*args, **kwargs):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from rpc.kernel import Kernel

    if len(sys.argv[1:]) > 1:
        health_port, submit_task_port, get_task_port = sys.argv[1:]
        kernel = Kernel(health_port=health_port,
                        submit_task_port=submit_task_port,
                        get_task_port=get_task_port)
    else:
        kernel = Kernel()

    kernel.register_handlers({'taxcalc_endpoint': taxcalc_endpoint})
    kernel.run()
```
