# Multiple-language Endpoint Submission Handler (MESH)

`mesh` facilitates cross platform development. Currently, this project is experimental, and we are actively working to improve its functionality and optimize its architecture. `mesh` should be easy to use, understand, modify, and extend. This project has been developed with two problems in mind:

- how to easily integrate a library written in Fortran with a library written in Python
- how to easily integrate Python libraries that are likely to have incompatible dependency requirements

We want to solve these problems in such a way that users need no knowledge of messaging queues, serialization techniques, or remote-procedure-protocols.

Approach
---------

`mesh` follows a client/kernel model where the client and kernel define a set of endpoints through which the user submits data through the client to the kernel and the kernel responds with the results from the function corresponding to that endpoint. Lucas has extended this approach by implementing a class proxy protocol on top of it which allows for the sequential management of state on the kernel side.

"kernel" is defined as a process that executes code upon request. A "client" facilitates the interaction between the user who is in one environment (and process) and a "kernel" which is in a different process and potentially different environment. This approach is based off of the Jupyter Notebook approach which is nicely summarized [here](https://medium.com/netflix-techblog/notebook-innovation-591ee3221233):

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

```python
from mesh.kernelmanager import KernelManager
from mesh.client import Client

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
    result = task.get()
    print(result)

```

The `taxcalc_kernel.py` module:

```python
def taxcalc_endpoint(*args, **kwargs):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from mesh.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel(health_port=health_port,
                    submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'taxcalc_endpoint': taxcalc_endpoint})
    kernel.run()
```

The class-proxy approach cuts through the complexity and exposure of implementation details of the approach shown above. With the class-proxy approach, it looks like this n the `Client` side:

```python
from mesh.client import TaskFailure
from mesh.kernelmanager import KernelManager
from mesh.proxy.client import ProxyClient, deref

kernel_info = {'new': {'module_path': 'kernel.py'}}

km = KernelManager(kernel_info)
km.start()
client = ProxyClient(kernel_id='new', serializer='pickle')

tc_proxy = client.get_remote('taxcalc')
rec = tc_proxy.Records.cps_constructor()
pol = tc_proxy.Policy()
reform = {2020: {'_II_em': [7000.0]}}
pol.implement_reform(reform)
calc = tc_proxy.Calculator(policy=pol, records=rec)
calc.advance_to_year(2020)
calc.calc_all()
m = calc.mtr('e00200p')
mtr = deref(m)
print('mtr for primary earner: ', mtr)

client.close()
km.close()
```


Examples
-----------

**OG-USA example**

OG-USA depends on Tax-Calculator for calculating marginal-tax-rates. In the past, these two projects' dependency requirements have become incompatible over brief windows of time. To run OG-USA during these periods of time, an out-of-date Tax-Calculator package would have to be used or OG-USA developers would have to rush to resolve the dependecy problem. We have been in search of a way to resolve this dependency problem with only a minimal amount of source-code intrusion.

Fortunately, OG-USA's primary interaction with Tax-Calculator can be isolated to one API call:

```python
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

In depth:

1. **Setup the OG-USA kernel:**
```python

def ogusa(*args, **kwargs):
    from ogusa.scripts import run_ogusa
    return run_ogusa.run_micro_macro(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from mesh.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel()

    kernel.register_handlers({'ogusa_endpoint': ogusa})
    kernel.run()
```
OG-USA is then setup to run in a conda environment `ospcdyn` defined in this [`environment.yml`](https://github.com/hdoupe/OG-USA/blob/91b1d7ffb19f88456da5d1188be151897dc1d4d0/environment.yml) file. Note that `taxcalc` is not in the dependency list. Until `mesh` is pushed to PyPi or conda, a local install using this repo will be necessary. This can be accomplished by navigating to the `pymesh` directory and running `pip install -e .`.

2. **Setup the Tax-Calculator kernel:**
```python
def ogusa_tc_endpoint(*args, **kwargs):
    import get_micro_data
    return get_micro_data.get_data(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from mesh.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel(health_port=health_port,
                    submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'ogusa_tc_endpoint': ogusa_tc_endpoint})
    kernel.run()
```
The module `get_micro_data.py` containing the function `get_data` and dependent functions is moved into the `examples` where it can be called from `taxcalc_kernel.py`, the kernel running Tax-Calculator.
The environment required the Tax-Calculator Kernel can be created from the following commands:
```
conda create -n taxcalc-env python=3.6 taxcalc
source activate taxcalc-env
pip install pyzmq msgpack
pip install -e . # from pymesh directory
```

3. **Finally, run commands against the OG-USA kernel:**
```python
from mesh.kernelmanager import KernelManager
from mesh.client import Client

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
The environment for this script requires: `mesh`, `pyzmq` and `msgpack` which can be installed with the following commands:
```bash
pip install pyzmq msgpack
pip install -e . # from pymesh directory
```

**TaxSim Example**

TaxSim is a fortran package and web interface with over 1000 citations on Google Scholar. It is currently maintained by Dan Feenberg. The fortran package `taxsim9.for` was written to be run from the command line and writes the resulting text file to `stdout`. Thus, some work was necessary in order to run it from a C script. Additions are:
- `ISO_C_BINDING` use to ease the interactions with C
- A function `runmodel` was added to wrap the main logic for running the script.
- A buffer is passed to `runmodel` and the results are written to it instead of the commandline
- Capability to pass either a full text file in a string or a path to a text file

I verified that the results did not change after these modifications by re-running the input data with the unmodified TaxSim package and comparing the results.

Please keep in mind that I am a novice C programmer and an even more novice Fortran programmer. That being said, I welcome all feedback and criticism. Also, I am sorry for what I have done to TaxSim. I am happy to discuss these changes more in depth.

The C kernel and its interface with TaxSim are less developed than the Python versions, but they provide a powerful example of the client/kernel and message-queue backed approach.

A `Dockerfile` is provided to link and build the C kernel. The `puf.csv` and `taxsim9.for` files are private and cannot be released. Other files may be released.

What are the parts that need to be assembled for this to work?
1. Build the docker file
2. Run the docker file
3. In a separate window, interact with the Kernel in Python (or any other available client)

In depth (steps 1 and 2 can be done without docker. See the [c-mesh install instructions](mesh/cmesh/README.md)):

1. **Build the Docker image:**
```bash
docker build -t cmeshkernel ./
```

2. **Run the Docker image:**
```bash
docker run -p 5566:5566 -p 5567:5567 -t cmeshkernel ./cmeshkernel
```

3. **In another window, Interact with the C kernel:**

```python
from io import StringIO

import pandas as pd
import matplotlib.pyplot as plt
import taxcalc

from mesh.client import Client
from mesh.serializers import receive_json, send_json

from data_prep import taxcalc_to_taxsim

# create taxcalc.Calculator instance to get necessary data for taxsim
rec = taxcalc.Records()
pol = taxcalc.Policy()
calc = taxcalc.Calculator(records=rec, policy=pol)
calc.calc_all()

# create PUF file that is compatible with TaxSim
taxsim_puf = taxcalc_to_taxsim(calc)

client = Client('taxsim', health_port='5566', submit_task_port='5567', get_task_port='5568', serializer='json')

args = {'mtr_wrt_group': 'full', 'file_name': taxsim_puf}
endpoint = 'taxsim'
task = client.submit(endpoint, args)
result = task.get()

df = pd.read_csv(StringIO(result), sep=' ', skipinitialspace=True)

plt.plot(df.State_Taxable_Income.values, df.srate/100, '.')

client.close()
```

Notes:
  - The C kernel has not been integrated with the `KernelManager` class.
  - There should be a `Makefile` for building this outside of Docker at least for Macs and Linux computers

Future Plans
-------------
In its current form, the Python components of this project are fairly solid and the Python-C-Fortran interaction is functional but could be refined.

Here are some things that I would like to do with the Python components:
- Add tests
- Add debugging support
- Shore up interactions with packages

Here's what I'd like to do with the C components:
- Re-write in C++ to better mirror the structure of the Python components

Overall package direction:
- Should the `mesh` kernels wrap kernels from the Jupyter ecosystem?
  - ex. [ipykernl](https://github.com/ipython/ipykernel), [IRKernel](https://github.com/IRkernel/IRkernel)
- What should the repo organization be?
  - Non-trivial amounts of code are required to actually apply the `mesh`. Should this code be re-organized as a downstream repo? For example, there could be a project built around managing the Tax-Calculator and OG-USA integration. Or, if we had a R implementation, there could be a package that manages the R interface for Tax-Calculator.
- Implement client/kernels for R and Julia
