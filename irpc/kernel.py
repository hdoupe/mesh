import time

import zmq
import msgpack

##############################################################################

def taxcalc_endpoint(year_n, start_year, use_puf_not_cps, use_full_sample,
                     user_mods):
    import taxcalc
    return taxcalc.tbi.run_nth_year_taxcalc_model(year_n, start_year,
                                                  use_puf_not_cps,
                                                  use_full_sample,
                                                  user_mods)


endpoints = {'taxcalc_endpoint': taxcalc_endpoint}


##############################################################################

def send_msgpack(socket, obj, flags=0):
    packed = msgpack.dumps(obj, use_bin_type=True)
    socket.send(packed, flags=flags)


def receive_msgpack(socket, flags=0):
    received = socket.recv(flags)
    return msgpack.loads(received, encoding='utf8', use_list=True)


def handler(m_bytes, socket):
    message = msgpack.loads(m_bytes, encoding='utf8', use_list=True)
    print(f'received message: {message}')
    out = {'job_id': message['job_id'], 'status': 'PENDING', 'result': False}
    send_msgpack(socket, out)
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
    send_msgpack(socket, out)
    assert socket.recv() == b'OK'


def start_mq():
    try:
        context = zmq.Context()
        health = context.socket(zmq.REP)
        health.bind("tcp://*:5556")

        worker_rep = context.socket(zmq.REP)
        worker_rep.bind("tcp://*:5557")

        worker_req = context.socket(zmq.REQ)
        worker_req.connect("tcp://localhost:5558")

        poller = zmq.Poller()
        poller.register(health, zmq.POLLIN)
        poller.register(worker_rep, zmq.POLLIN)

        while True:
            socks = dict(poller.poll())
            if health in socks:
                health.recv()
                health.send(b'OK')
            if worker_rep in socks:
                message = worker_rep.recv()
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
    start_mq()
