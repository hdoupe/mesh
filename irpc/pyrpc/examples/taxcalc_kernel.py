

def taxcalc_endpoint(year_n, start_year, use_puf_not_cps, use_full_sample,
                     user_mods, return_dict):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(year_n, start_year,
                                                  use_puf_not_cps,
                                                  use_full_sample,
                                                  user_mods,
                                                  return_dict)


if __name__ == '__main__':
    import sys
    from rpc.kernel import Kernel

    if len(sys.argv[1:]) > 1:
        health_port, rep_port, req_port = sys.argv[1:]
        kernel = Kernel(health_port=health_port, rep_port=rep_port,
                        req_port=req_port)
    else:
        kernel = Kernel()

    kernel.register_handlers({'taxcalc_endpoint': taxcalc_endpoint})
    kernel.run()
