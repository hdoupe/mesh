import os

from mesh.proxy.client import ProxyClient
from mesh.kernelmanager import KernelManager

def test_proxy():
    path = os.path.abspath(os.path.dirname(__file__))
    kernel_info = {
        'testobj': {'module_path': os.path.join(path, 'kernels/proxykernel1.py')}
    }
    with KernelManager(kernel_info) as km:
        client = ProxyClient(kernel_id='testobj', serializer='pickle')
        proxy = client.get_remote('testobj')
        r = proxy.mult(1, 2)
        assert r == 2
        r = proxy.mult(1.0, 2)
        assert r == 2.0
        proxy.a = 2
        print(proxy.a)
        client.close()
