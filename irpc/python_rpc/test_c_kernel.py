from client import Client
from serializers import receive_json, send_json


args = {'mtr_wrt_group': 'full', 'file_name': 'taxsimrun.txt'}
endpoint = 'taxsim'

with Client(health_port='5566', submit_job_port='5567',
            get_job_port='5568') as client:
    job_id = client.submit(endpoint, args, send_func=send_json)
    result = client.get(job_id, receive_func=receive_json)
    print(result)
