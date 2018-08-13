# I-Remote-Procedure-Call

`irpc` facilitates cross platform development. Currently, this project
is experimental and we are actively working to improve its functionality
and optimize its architecture. `irpc` should be easy to use, easy to
understand, and easy to modify. This project has been developed with two
problems in mind:

- how to easily integrate a library written in Fortran with a library written
  in Python
- how to easily integrate Python libraries that are likely to have incompatible
  dependency requirements

We want to solve this problems in such a way that users need no knowledge of
messaging queues, serialization techniques, or remote-procedure-protocols.

Inspiration was drawn from the client-kernel model of the IPykernel/Jupyter
ecosystem, RPC packages such as PyRPC, and Dask's task submission patterns.

# Examples

- C- Test via*:

Build and Start C kernel:
```
docker build -t taxsimlink ./
docker run -p 5566:5566 -p 5567:5567 -t taxsimlink ./linked
```

Post jobs to kernel:
```
from io import StringIO

from client import Client
from serializers import receive_json, send_json
import pandas as pd

args = {'mtr_wrt_group': 'full', 'file_name': 'puf_taxsim.txt'}
endpoint = 'taxsim'

with Client(health_port='5566', submit_job_port='5567',
            get_job_port='5568') as client:
    job_id = client.submit(endpoint, args, send_func=send_json)
    result = client.get(job_id, receive_func=receive_json)

    df = pd.read_csv(StringIO(result), sep=' ', skipinitialspace=True)
```

\* email me if interested in the `taxsim9.for` and `taxsimrun.txt` files

- Two Python libraries:
...
