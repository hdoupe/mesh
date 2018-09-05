def endpoint1(*args, **kwargs):
    import time
    time.sleep(2)
    return 'hello, world!'


def identity(*args, **kwargs):
    import time
    time.sleep(1.5)
    return 'I am kernel 1'


if __name__ == '__main__':
    import sys
    from mesh.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel(health_port=health_port,
                    submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'endpoint1': endpoint1, 'identity': identity})
    kernel.run()
