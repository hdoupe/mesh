import uuid
import time

import zmq
import msgpack


def health_check(health_socket):
    health_socket.send(b'')
    return health_socket.recv() == b'OK'


def get_sockets(context=None, health_port='5566', submit_job_port='5567',
                get_job_port='5568'):
    if context is None:
        context = zmq.Context()

    health = context.socket(zmq.REQ)
    health.connect(f"tcp://localhost:{health_port}")

    submit_job = context.socket(zmq.REQ)
    submit_job.connect(f"tcp://localhost:{submit_job_port}")

    get_job = context.socket(zmq.REP)
    get_job.bind(f"tcp://*:{get_job_port}")

    poller = zmq.Poller()
    poller.register(get_job)

    assert health_check(health)

    return (context, health, submit_job, get_job, poller)


def send_msgpack(socket, obj, flags=0):
    packed = msgpack.dumps(obj, use_bin_type=True)
    return socket.send(packed, flags=flags)


def receive_msgpack(socket, flags=0):
    received = socket.recv(flags)
    return msgpack.loads(received, encoding='utf8', use_list=True)


def submit(socket, endpoint, args):
    job_id = str(uuid.uuid4())
    data = {'job_id': job_id,
            'endpoint': endpoint,
            'args': args}
    print('submitting data', data)
    send_msgpack(socket, data)
    assert socket.recv() == b'OK'
    return job_id


def get(socket, poller, job_id):
    message = None
    result = None
    status = 'PENDING'
    while status == 'PENDING':
        socks = dict(poller.poll())
        if socket in socks:
            message = receive_msgpack(socket)
            print(f'received message: {message}')
            socket.send(b'OK')
            if message['job_id'] == job_id:
                status = message['status']
                result = message['result']
            else:
                raise IOError(f"received unexpected job id: {message['job_id']}")
    return result


def test():
    (context, health, submit_job, get_job, poller) = get_sockets()
    try:
        print('healthy')
        assert health_check(health)
        print('packing')
        send_msgpack(submit_job, {'test': '12'})
        msg = submit_job.recv()
        print(f'pack got: {msg}')
    except KeyboardInterrupt:
        print('W: interupt received, stopping')
    finally:
        print('closing out...')
        health.close()
        submit_job.close()
        get_job.close()
        context.term()


if __name__ == '__main__':
    # endpoint = 'taxcalc_endpoint'
    # args = [
    #     0,
    #     2017,
    #     False,
    #     False,
    #     {'policy': {2020: {'_SS_Earnings_c': [15000.0]}},
    #      'consumption': {},
    #      'behavior': {},
    #      'growdiff_baseline': {},
    #      'growdiff_response': {},
    #      'growmodel': {}}
    # ]
    # result = run_endpoint(endpoint, args)
    # print(result)
    test()
