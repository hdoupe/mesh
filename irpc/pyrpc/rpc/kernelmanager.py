from contextlib import contextmanager

import subprocess as sp
import concurrent.futures

from rpc.client import Client
import time



class KernelManager():

    def __init__(self, kernel_info):
        self.kernel_info = kernel_info
        self.n_threads = len(self.kernel_info)

        self.procs_out = 0

    def run_kernels(self):
        self.executor = concurrent.futures.ThreadPoolExecutor(self.n_threads)
        cmds = []
        for info in self.kernel_info:
            executable = info['executable']
            module_path = info['module_path']
            health_sock = str(info['health_sock'])
            rep_sock = str(info['rep_sock'])
            req_sock = str(info['req_sock'])
            argv = ' '.join([executable, module_path, health_sock, rep_sock,
                             req_sock])
            cmds.append(argv)
        self.executor.map(self.run, cmds)

    def close(self):
        if hasattr(self, 'executor'):
            print('shutting down')
            try:
                # waiting on a ctr-C
                while True:
                    time.sleep(.1)
            finally:
                self.executor.shutdown()
                print('finished...')
        else:
            raise ValueError("Executor object was never instantiated!")

    def run(self, cmd):
        """
        Run shell commands, make sure they return with status '0'
        """
        try:
            sp.run([cmd], shell=True, check=True)
        except KeyboardInterrupt:
            pass
        finally:
            return

    def __enter__(self):
        self.run_kernels()
        return self

    def __exit__(self, *exc):
        self.close()


if __name__ == '__main__':
    health, rep, req = 5566, 5567, 5568
    kernel_info = [
        {'name': 'taxcalc1',
         'executable': '/Users/henrydoupe/anaconda3/envs/taxcalc-dev/bin/python',
         'module_path': '../taxcalc_kernel.py',
         'health_sock': 5566,
         'rep_sock': 5567,
         'req_sock': 5568},
        {'name': 'taxcalc2',
         'executable': '/Users/henrydoupe/anaconda3/bin/python',
         'module_path': '../taxcalc_kernel.py',
         'health_sock': 5576,
         'rep_sock': 5577,
         'req_sock': 5578},
        {'name': 'taxcalc3',
         'executable': '/Users/henrydoupe/anaconda3/bin/python',
         'module_path': '../taxcalc_kernel.py',
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
