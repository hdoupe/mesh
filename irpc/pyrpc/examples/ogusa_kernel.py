
def ogusa(*args, **kwargs):
    from ogusa.scripts import run_ogusa
    return run_ogusa.run_micro_macro(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from rpc.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel()

    kernel.register_handlers({'ogusa_endpoint': taxcalc_endpoint})
    kernel.run()
