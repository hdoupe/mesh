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
        for info in self.kernel_info:
            executable = info['executable']
            module_path = info['module_path']
            health_sock = str(info['health_sock'])
            rep_sock = str(info['rep_sock'])
            req_sock = str(info['req_sock'])
            argv = ' '.join([executable, module_path, health_sock, rep_sock,
                             req_sock])
            proc = sp.Popen([argv], shell=True)
            self.procs.append(proc)

    def close(self):
        while len(self.procs) > 0:
            proc = self.procs.pop()
            proc.send_signal(signal.SIGINT)

    def __enter__(self):
        self.run_kernels()
        return self

    def __exit__(self, *exc):
        self.close()

    def read_kernel_info(self, kernel_info):
        sock_base = 5566
        sock_mult = 0
        socks = ['health_sock', 'rep_sock', 'req_sock']
        keyset = set(socks + ['name', 'executable', 'module_path'])
        for i in range(len(kernel_info)):
            info = kernel_info[i]
            if 'executable' not in info:
                info['executable'] = sys.executable
            for j in range(len(socks)):
                if socks[j] not in info:
                    info[socks[j]] = sock_base + j + 10 * i
            print(info)
            assert keyset == set(info.keys())
        return kernel_info
