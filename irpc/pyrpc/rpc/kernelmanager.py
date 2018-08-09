import subprocess as sp
import signal

from rpc.client import Client


class KernelManager():

    def __init__(self, kernel_info):
        self.kernel_info = kernel_info
        self.n_threads = len(self.kernel_info)
        self.executor = None
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
