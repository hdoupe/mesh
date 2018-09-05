from mesh.kernelmanager import KernelManager
from mesh.client import Client

kernel_info = {
    'taxcalc': {
        'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-env/bin/python',
        'module_path': 'taxcalc_kernel.py'
    },
    'ogusa': {
        'executable': '/Users/henrydoupe/anaconda3/envs/ospcdyn/bin/python',
        'module_path': 'ogusa_kernel.py'
     }
}


with KernelManager(kernel_info) as sk:
    print('running tasks...')
    user_params={
        'reform':{
            2020: {
                '_STD': [15000, 30000, 15000, 22000, 30000]
            }
        }
    }
    with Client(kernel_id='ogusa') as client:
        task = client.submit_task('ogusa_endpoint',
                                  args=(),
                                  kwargs={'user_params': user_params})
        result = task.get()
