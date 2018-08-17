from rpcproxy.kernel import ProxyKernel

import taxcalc

ker = ProxyKernel({'taxcalc': taxcalc}, serializer='pickle')
ker.run()
