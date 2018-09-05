from mesh.client import TaskFailure
from mesh.kernelmanager import KernelManager
from mesh.proxy.client import ProxyClient, deref

kernel_info = {'new': {'module_path': 'kernel.py'}}

km = KernelManager(kernel_info)
km.start()
client = ProxyClient(kernel_id='new', serializer='pickle')

tc_proxy = client.get_remote('taxcalc')
rec = tc_proxy.Records.cps_constructor()
pol = tc_proxy.Policy()
reform = {2020: {'_II_em': [7000.0]}}
pol.implement_reform(reform)
calc = tc_proxy.Calculator(policy=pol, records=rec)
calc.advance_to_year(2020)
calc.calc_all()
m = calc.mtr('e00200p')
mtr = deref(m)
print('mtr for primary earner: ', mtr)

client.close()
km.close()
