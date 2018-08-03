import time

import zmq
import msgpack

from rpc.serializers import (send_msgpack, send_json, send_pickle,
                          receive_msgpack, receive_json, receive_pickle)

##############################################################################


def taxcalc_endpoint(year_n, start_year, use_puf_not_cps, use_full_sample,
                     user_mods, return_dict):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(year_n, start_year,
                                                  use_puf_not_cps,
                                                  use_full_sample,
                                                  user_mods,
                                                  return_dict)


endpoints = {'taxcalc_endpoint': taxcalc_endpoint}


##############################################################################

def handler(message, socket):
    print(f'received message: {message}')
    out = {'job_id': message['job_id'], 'status': 'PENDING', 'result': False}
    send_pickle(socket, out)
    print('waiting on response...')
    assert socket.recv() == b'OK'
    print('running job...')
    try:
        result = endpoints[message['endpoint']](*message['args'])
        status = 'SUCCESS'
    except Exception as e:
        result = e.__str__()
        status = 'FAILURE'

    out = {'job_id': message['job_id'], 'status': status, 'result': result}
    print('publish: ', out)
    send_pickle(socket, out)
    assert socket.recv() == b'OK'


def start_mq(health_port='5566', rep_port='5567', req_port='5568'):
    try:
        context = zmq.Context()

        health = context.socket(zmq.REP)
        health.bind(f"tcp://*:{health_port}")

        worker_rep = context.socket(zmq.REP)
        worker_rep.bind(f"tcp://*:{rep_port}")

        worker_req = context.socket(zmq.REQ)
        worker_req.connect(f"tcp://localhost:{req_port}")

        poller = zmq.Poller()
        poller.register(health, zmq.POLLIN)
        poller.register(worker_rep, zmq.POLLIN)

        while True:
            socks = dict(poller.poll())
            if health in socks:
                health.recv()
                health.send(b'OK')
            if worker_rep in socks:
                message = receive_pickle(worker_rep)
                worker_rep.send(b'OK')
                handler(message, worker_req)

    except KeyboardInterrupt:
        print("W: interrupt received, stopping…")
    finally:
        # clean up
        health.close()
        worker_req.close()
        worker_rep.close()
        context.term()


if __name__ == '__main__':
    import sys
    if len(sys.argv[1:]) > 1:
        health_port, rep_port, req_port = sys.argv[1:]
        start_mq(health_port, rep_port, req_port)
    else:
        start_mq()
