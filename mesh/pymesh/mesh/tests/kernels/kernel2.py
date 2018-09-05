def identity(*args, **kwargs):
    import time
    time.sleep(1)
    return 'I am kernel 2'


if __name__ == '__main__':
    import sys
    from mesh.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    kernel = Kernel(health_port=health_port,
                    submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'identity': identity})
    kernel.run()
