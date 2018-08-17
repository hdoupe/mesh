

def taxcalc_endpoint(*args, **kwargs):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(*args, **kwargs)


def ogusa_tc_endpoint(*args, **kwargs):
    import ogusa_tc_interface
    return ogusa_tc_interface.get_data(*args, **kwargs)

if __name__ == '__main__':
    import sys
    from rpc.kernel import Kernel

    health_port, submit_task_port, get_task_port = sys.argv[1:]
    print('stating kernel at ports: ', health_port, submit_task_port, get_task_port)
    kernel = Kernel(health_port=health_port, submit_task_port=submit_task_port,
                    get_task_port=get_task_port)

    kernel.register_handlers({'taxcalc_endpoint': taxcalc_endpoint,
                              'ogusa_tc_endpoint': ogusa_tc_endpoint})
    kernel.run()
