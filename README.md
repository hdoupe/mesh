# I-Remote-Procedure-Call

- Python- Test via [out of date]:

Terminal window 1:
`python kernel.py`

Terminal window 2:
`python client.py`

- C- Test via:

Build and Start C kernel:
`docker build -t taxsimlink ./`
`docker run -p 5566:5566 -p 5567:5567 -t taxsimlink ./linked`

Post jobs to kernel:
```
from client import Client
from serializers import receive_json, send_json


args = {'mtr_wrt_group': 'full', 'file_name': 'taxsimrun.txt'}
endpoint = 'taxsim'

try:
    client = Client(health_port='5566', submit_job_port='5567',
                    get_job_port='5568')
    job_id = client.submit(endpoint, args, send_func=send_json)
    result = client.get(job_id, receive_func=receive_json)
    print(result)
finally:
    client.close()
```
