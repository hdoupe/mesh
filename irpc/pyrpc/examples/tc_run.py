from rpc.kernelmanager import KernelManager
from rpc.client import Client


health, rep, req = 5566, 5567, 5568
kernel_info = {
    'taxcalc1': {
     'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-dev/bin/python',
     'module_path': 'taxcalc_kernel.py'},
    'taxcalc2': {
     'module_path': 'taxcalc_kernel.py'},
    'taxcalc3': {
     'executable': '/Users/henrydoupe/anaconda3/bin/python',
     'module_path': 'taxcalc_kernel.py'},
}

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
    for id in kernel_info:
        print('getting client: ', id)
        client = Client(kernel_id=id)
        print('got client')
        t = client.submit(endpoint, args)
        print(t)
        r = client.get(t)
        print(r)
        client.close()
        print('closing client...')
