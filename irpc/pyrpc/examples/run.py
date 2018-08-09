from rpc.kernelmanager import KernelManager
from rpc.client import Client

health, rep, req = 5566, 5567, 5568
kernel_info = [
    {'name': 'taxcalc1',
     'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-dev/bin/python',
     'module_path': 'taxcalc_kernel.py',
     'health_sock': 5566,
     'rep_sock': 5567,
     'req_sock': 5568},
    {'name': 'taxcalc2',
     'executable': '/Users/henrydoupe/anaconda3/bin/python',
     'module_path': 'taxcalc_kernel.py',
     'health_sock': 5576,
     'rep_sock': 5577,
     'req_sock': 5578},
    {'name': 'taxcalc3',
     'executable': '/Users/henrydoupe/anaconda3/bin/python',
     'module_path': 'taxcalc_kernel.py',
     'health_sock': 5586,
     'rep_sock': 5587,
     'req_sock': 5588}
]

endpoint = 'taxcalc_endpoint'
args = [
    0,
    2017,
    False,
    False,
    {'policy': {2020: {'_SS_Earnings_c': [15000.0]}},
     'consumption': {},
     'behavior': {},
     'growdiff_baseline': {},
     'growdiff_response': {},
     'growmodel': {}},
    False
]

with KernelManager(kernel_info) as sk:
    print('running tasks...')
    for info in kernel_info:
        print('getting client: ', info)
        client = Client(health_port=info['health_sock'],
                        submit_job_port=info['rep_sock'],
                        get_job_port=info['req_sock'])
        print('got client')
        t = client.submit(endpoint, args)
        print(t)
        r = client.get(t)
        print(r)
        client.close()
        print('closing client...')
