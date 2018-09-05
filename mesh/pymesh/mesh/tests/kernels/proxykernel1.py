from mesh.proxy.kernel import ProxyKernel

class Obj():
    def mult(a, b):
        return a * b

ker = ProxyKernel({'testobj': Obj}, serializer='pickle')
ker.run()
