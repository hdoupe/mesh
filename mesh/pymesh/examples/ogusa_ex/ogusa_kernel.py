
def ogusa_endpoint(*args, **kwargs):
    from ogusa.scripts import run_ogusa
    return run_ogusa.run_micro_macro(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from mesh.kernel import Kernel
    health_port, submit_task_port, get_task_port = sys.argv[1:]
    print('stating kernel at ports: ', health_port, submit_task_port, get_task_port)
    kernel = Kernel(health_port=health_port, submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'ogusa_endpoint': ogusa_endpoint})
    kernel.run()
