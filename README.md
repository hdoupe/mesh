# Glue/Remote-Kernel-Protocol+ (RKP(P)/ reads as: "Remote Kernel Protocol Plus")/IRPC

`irpc` facilitates cross platform development. Currently, this project is experimental, and we are actively working to improve its functionality and optimize its architecture. `irpc` should be easy to use, understand, modify, and extend. This project has been developed with two problems in mind:

- how to easily integrate a library written in Fortran with a library written in Python
- how to easily integrate Python libraries that are likely to have incompatible dependency requirements

We want to solve this problems in such a way that users need no knowledge of messaging queues, serialization techniques, or remote-procedure-protocols.

Approach
---------

`irpc` follows a client/kernel model where the client and kernel define a set of endpoints through which the user submits data through the client to the kernel and the kernel responds with the results from the function corresponding to that endpoint. Lucas has extended this approach by implementing a class proxy protocol on top of it which allows for the sequential management of state on the kernel side.

"kernel" is defined as a process that executes code upon request. A "client" facilitates the interaction between the user who is in one environment (and process) and a "kernel" which is in a different process and potentially different environment. This approach is based off of the Jupyter Notebook approach which is nicely summarized (here)[https://medium.com/netflix-techblog/notebook-innovation-591ee3221233]:

> The Jupyter protocol provides a standard messaging API to communicate with kernels that act as computational engines. The protocol enables a composable architecture that separates where content is written (the UI) and where code is executed (the kernel). By isolating the runtime from the interface, notebooks can span multiple languages while maintaining flexibility in how the execution environment is configured. If a kernel exists for a language that knows how to communicate using the Jupyter protocol, notebooks can run code by sending messages back and forth with that kernel.

Thus, the client and kernel do not need to be in the same language or computing environment. So far, this project has successfully integrated Python and Fortran libraries as well as Python libraries in different conda environments. The upside of this approach is that you could simultaneously run kernels in R, C, Fortran (with C-bindings), and Python. The user could spin up a client for each kernel and submit data to them. The kernels could even spin up clients to communicate with kernels written in other languages. Note that the same kernel can accept data from clients in multiple languages. That is, special kernels for the Python-to-R interaction and another for the Python-to-Fortran interaction are not needed. Only a Python kernel with the correct endpoints is needed.

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

What are the parts that need to be assembled for this to work?
1. There needs to be an OG-USA kernel to which the user can submit OG-USA parameters
2. There needs to be a Tax-Calculator kernel to run the taxcalc API calls in `get_micro_data.py`. OG-USA spins up a client to submit data to this kernel and retrieve results from it in `txfunc.py`.
3. The user needs to initiate this process via with
     - a `KernelManager` to start the kernels described in (1) and (2)
     - a `Client` to submit data from the user to the OG-USA `kernel` described in (1)

1. Setup the OG-USA kernel:
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
OG-USA is then setup to run in a conda environment `ospcdyn` defined in this [`environment.yml`](https://github.com/hdoupe/OG-USA/blob/91b1d7ffb19f88456da5d1188be151897dc1d4d0/environment.yml) file. Note that `taxcalc` is not in the dependency list. Until `irpc` is pushed to PyPi or conda, a local install using this repo will be necessary. This can be accomplished by navigating to the `pyrpc` directory and running `pip install -e .`.  

2. Setup the Tax-Calculator kernel:
```
def ogusa_tc_endpoint(*args, **kwargs):
    import get_micro_data
    return get_micro_data.get_data(*args, **kwargs)

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
The module `get_micro_data.py` containing the function `get_data` and dependent functions is moved into the `examples` where it can be called from `taxcalc_kernel.py`, the kernel running Tax-Calculator.
The environment required the Tax-Calculator Kernel can be created from the following commands:
```
conda create -n taxcalc-env python=3.6 taxcalc
source activate taxcalc-env
pip install pyzmq msgpack
pip install -e . # from pyrpc directory
```

3. Finally, run commands against the OG-USA kernel:
```
from rpc.kernelmanager import KernelManager
from rpc.client import Client

kernel_info = [
    'taxcalc': {
        'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-env/bin/python',
        'module_path': 'taxcalc_kernel.py'
    },
    'ogusa': {
        'executable': '/Users/henrydoupe/anaconda3/envs/ospcdyn/bin/python',
        'module_path': 'ogusa_kernel.py'
     }
]

with KernelManager(kernel_info) as sk:
    print('running tasks...')
    user_params={
        'reform':{
            2020: {
                '_STD': [15000, 30000, 15000, 22000, 30000]
            }
        }
    }
    client = Client(kernel_id='ogusa')
    task = client.submit('ogusa_endpoint', kwargs={'user_params': user_params})
    result = task.get()
```
The environment for this script requires: `irpc`, `pyzmq` and `msgpack` which can be installed with the following commands:
```
pip install pyzmq msgpack
pip install -e . # from pyrpc directory
```