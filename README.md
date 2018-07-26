# I-Remote-Procedure-Call

- Python- Test via [out of date]:

Terminal window 1:
`python kernel.py`

Terminal window 2:
`python client.py`

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
