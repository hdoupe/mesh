import os

from mesh.client import Client
from mesh.kernelmanager import KernelManager


def test_client():
    path = os.path.abspath(os.path.dirname(__file__))
    kernel_info = {
        'kernel1': {
            'module_path': os.path.join(path, 'kernels/kernel1.py'),
        }
    }
    with KernelManager(kernel_info) as km:
        client = Client(kernel_id='kernel1')
        task = client.submit('endpoint1')
        result = task.get()
        assert result == 'hello, world!'
        client.close()
        assert client.context.closed
        assert client.health_sock.closed
        assert client.sub_sock.closed
        assert client.get_sock.closed


def test_client_multi_kernels():
    path = os.path.abspath(os.path.dirname(__file__))
    kernel_info = {
        'kernel1': {
            'module_path': os.path.join(path, 'kernels/kernel1.py'),
        },
        'kernel2': {
            'module_path': os.path.join(path, 'kernels/kernel2.py'),
        }
    }
    with KernelManager(kernel_info) as km:
        with Client(kernel_id='kernel1') as client:
            task = client.submit('identity')
            result = task.get()
            assert result == 'I am kernel 1'

        with Client(kernel_id='kernel2') as client:
            result = client.do_task('identity')
            assert result == 'I am kernel 2'
