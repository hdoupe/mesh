from rpc.proxy.kernel import ProxyKernel


class Test:
    def some_method(self):
        return "aa"

    def another_method(self):
        import taxcalc
        return taxcalc.Records.cps_constructor().e00200.tolist()

    def failing_method(self):
        raise AssertionError("foo")


ker = ProxyKernel({'Test': Test})
ker.run()
