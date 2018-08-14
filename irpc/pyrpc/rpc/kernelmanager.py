import subprocess as sp
import signal
import sys
import concurrent.futures

import zmq

from rpc.serializers import send_json, receive_json


def get_kernel_config(kernel_info, kernel_id):
    """
    Grab ports to spin up corresponding client
    """
    if kernel_id in kernel_info:
        return {
            'status': 'SUCCESS',
            'health_port': kernel_info[kernel_id]['health_port'],
            'submit_task_port': kernel_info[kernel_id]['submit_task_port'],
            'get_task_port': kernel_info[kernel_id]['get_task_port']
        }
    else:
        return {'status': 'FAILURE'}


def config_listener(port, kernel_config):
    context = zmq.Context.instance()
    listener = context.socket(zmq.REP)
    listener.bind(f'tcp://*:{port}')
    shutdown = context.socket(zmq.PAIR)
    shutdown.connect('inproc://comm')
    poller = zmq.Poller()
    poller.register(listener, zmq.POLLIN)
    poller.register(shutdown, zmq.POLLIN)

    while True:
        socks = dict(poller.poll())
        if listener in socks:
            msg = receive_json(listener)
            config = get_kernel_config(kernel_config, msg['kernel_id'])
            send_json(listener, config)
        if shutdown in socks:
            shutdown.recv()
            send_json(shutdown, {'status': 'SUCCESS'})
            break

    listener.close()
    shutdown.close()

class KernelManager():

    def __init__(self, kernel_info, config_port=8080):
        self.kernel_info = self.read_kernel_info(kernel_info)
        self.procs = []
        self.executor = None
        self.config_port = int(config_port)
        self.start_config_listener()

    def run_kernels(self):
        """
        Spin up kernel for each item in `kernel_info` dict
        """
        for name, info in self.kernel_info.items():
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

        self.shutdown_config_listener()

    def read_kernel_info(self, kernel_info):
        """
        Validate `kernel_info` dict and specify ports if not done already
        """
        port_base = 5566
        port_mult = 0
        ports = ['health_port', 'submit_task_port', 'get_task_port']
        keyset = set(ports + ['executable', 'module_path'])
        for i, id in enumerate(kernel_info):
            info = kernel_info[id]
            if 'executable' not in info:
                info['executable'] = sys.executable
            for j in range(len(ports)):
                if ports[j] not in info:
                    info[ports[j]] = port_base + j + 10 * i
            assert keyset == set(info.keys())
        return kernel_info

    def start_config_listener(self):
        """
        Starts listener for clients to query about ports, shutdown via signal
        over zmq.PAIR socket. See http://zguide.zeromq.org/py:mtrelay for
        pattern
        """
        self.context = zmq.Context.instance()
        self.shutdown = self.context.socket(zmq.PAIR)
        self.shutdown.bind('inproc://comm')
        self.executor = concurrent.futures.ThreadPoolExecutor(1)
        self.executor.submit(config_listener, self.config_port,
                             self.kernel_info)

    def shutdown_config_listener(self):
        """
        Shutdown client listener, clean up sockets, join thread
        """
        self.shutdown.send(b'')
        status = receive_json(self.shutdown)
        assert status['status'] == 'SUCCESS'
        self.shutdown.close()
        self.context.term()
        self.executor.shutdown()


    def __enter__(self):
        self.run_kernels()
        return self

    def __exit__(self, *exc):
        self.close()
