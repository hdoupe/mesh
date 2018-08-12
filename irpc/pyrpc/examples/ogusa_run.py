import ogusa

from rpc.kernelmanager import KernelManager
from rpc.client import Client

from run_ogusa_example import run_micro_macro

health, rep, req = 5566, 5567, 5568
kernel_info = [
    {'name': 'taxcalc1',
     'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-env/bin/python',
     'module_path': 'taxcalc_kernel.py'},
]


with KernelManager(kernel_info) as sk:
    print('running tasks...')
    run_micro_macro(user_params={
        'reform':{
            2020: {
                '_STD': [15000, 30000, 15000, 22000, 30000]
            }
        }
    })
