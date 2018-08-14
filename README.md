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
        'module_path': 'taxcalc_kernel.py',
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

The class-proxy approach cuts through the complexity and exposure of implementation details of the approach shown above. With the class-proxy approach, it looks like this n the `Client` side:

```
from rpc.client import Client
from rpc.kernelmanager import KernelManager
from client import get_remote, deref
import itertools

kernel_info = {'new': {'module_path': 'kernel.py'}}

with KernelManager(kernel_info) as km:
    with Client(kernel_id='new', serializer='msgpack') as cli:
        TaxcalcProxy = get_remote(cli, 'taxcalc')
        tcproxy = TaxcalcProxy()
        result = tcproxy.run_nth_year_taxcalc(*args, **kwargs)
```


Examples
-----------

**OG-USA example**

OG-USA depends on Tax-Calculator for calculating marginal-tax-rates. In the past, these two projects' dependency requirements have become incompatible over brief windows of time. To run OG-USA during these periods of time, an out-of-date Tax-Calculator package would have to be used or OG-USA developers would have to rush to resolve the dependecy problem. We have been in search of a way to resolve this dependency problem with only a minimal amount of source-code intrusion.

Fortunately, OG-USA's primary interaction with Tax-Calculator can be isolated to one API call:

```
micro_data = get_micro_data.get_data(baseline=baseline,
                                     start_year=beg_yr,
                                     reform=reform, data=data,
                                     client=client,
                                     num_workers=num_workers) 
```

The module `get_micro_data.py` containing the function `get_data` and dependent functions was moved into the current working directory where it can be called from the kernel running Tax-Calculator.

OG-USA is then setup to run in a conda environment `ospcdyn` defined in this [`environment.yml`](https://github.com/hdoupe/OG-USA/blob/91b1d7ffb19f88456da5d1188be151897dc1d4d0/environment.yml) file. Note that `taxcalc` is not in the dependency list. Finally, in the `pyrpc` directory, run `pip install -e .` to create a local installation of the `irpc` package.

Setup the Tax-Calculator kernel:

```

def taxcalc_endpoint(*args, **kwargs):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(*args, **kwargs)


def ogusa_tc_endpoint(*args, **kwargs):
    import ogusa_tc_interface
    return ogusa_tc_interface.get_data(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from rpc.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel(health_port=health_port,
                    submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'taxcalc_endpoint': taxcalc_endpoint,
                              'ogusa_tc_endpoint': ogusa_tc_endpoint})
    kernel.run()
```

The environment required for this file can be created from the following commands:
```
conda create -n taxcalc-env python=3.6 taxcalc
source activate taxcalc-env
pip install pyzmq msgpack
```

To setup the kernel for OG-USA, use the following script:

```

def ogusa(*args, **kwargs):
    from ogusa.scripts import run_ogusa
    return run_ogusa.run_micro_macro(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from rpc.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel()

    kernel.register_handlers({'ogusa_endpoint': taxcalc_endpoint})
    kernel.run()
```

