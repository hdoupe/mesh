import subprocess as sp
import signal
import sys

from rpc.client import Client


class KernelManager():

    def __init__(self, kernel_info):
        self.kernel_info = self.read_kernel_info(kernel_info)
        self.n_threads = len(self.kernel_info)
        self.procs = []

    def run_kernels(self):
        """
        Spin up kernel for each item in `kernel_info` dict
        """
        for info in self.kernel_info:
            executable = info['executable']
            module_path = info['module_path']
            argv = ' '.join([executable, module_path,
                             str(info['health_port']),
                             str(info['submit_task_port']),
                             str(info['get_task_port'])])
            proc = sp.Popen([argv], shell=True)
            self.procs.append(proc)

    def close(self):
        """
        Send Ctrl-C to subprocesses that are still alive
        """
        while len(self.procs) > 0:
            proc = self.procs.pop()
            proc.send_signal(signal.SIGINT)

    def read_kernel_info(self, kernel_info):
        """
        Validate `kernel_info` dict and specify ports if not done already
        """
        port_base = 5566
        port_mult = 0
        ports = ['health_port', 'submit_task_port', 'get_task_port']
        keyset = set(ports + ['kernel_id', 'executable', 'module_path'])
        for i in range(len(kernel_info)):
            info = kernel_info[i]
            if 'executable' not in info:
                info['executable'] = sys.executable
            for j in range(len(ports)):
                if ports[j] not in info:
                    info[ports[j]] = ports_base + j + 10 * i
            print(info)
            assert keyset == set(info.keys())
        return kernel_info

    def get_kernel_config(self, kernel_id):
        """
        Grab ports to spin up corresponding client
        """
        return {self.kernel_info['health_port'],
                self.kernel_info['submit_task_port'],
                self.kernel_info['get_task_port']}

    def __enter__(self):
        self.run_kernels()
        return self

    def __exit__(self, *exc):
        self.close()
