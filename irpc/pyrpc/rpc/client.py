import uuid

import zmq

from .serializers import receive_msgpack, send_msgpack


class Client():

    def __init__(self, context=None, health_port='5566',
                 submit_job_port='5567', get_job_port='5568'):
        self.context = context or zmq.Context()
        self.set_sockets(health_port, submit_job_port, get_job_port)

    def set_sockets(self, health_port='5566', submit_job_port='5567',
                    get_job_port='5568'):
        self.health_sock = self.context.socket(zmq.REQ)
        self.health_sock.connect(f"tcp://127.0.0.1:{health_port}")

        self.sub_sock = self.context.socket(zmq.REQ)
        self.sub_sock.connect(f"tcp://127.0.0.1:{submit_job_port}")

        self.get_sock = self.context.socket(zmq.REP)
        self.get_sock.bind(f"tcp://*:{get_job_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.get_sock)

        assert self.health_check()

    def submit(self, endpoint, args, send_func=send_msgpack):
        job_id = str(uuid.uuid4())
        data = {'job_id': job_id,
                'endpoint': endpoint,
                'args': args}
        # print('submitting data', data)
        send_func(self.sub_sock, data)
        assert self.sub_sock.recv() == b'OK'
        return job_id

    def get(self, job_id, receive_func=receive_msgpack):
        message = None
        result = None
        status = 'PENDING'
        while status == 'PENDING':
            socks = dict(self.poller.poll())
            if self.get_sock in socks:
                message = receive_func(self.get_sock)
                print(f"received message {message['job_id']}: {message['status']}")
                self.get_sock.send(b'OK')
                if message['job_id'] == job_id:
                    status = message['status']
                    result = message['result']
                else:
                    e_msg = f"received unexpected job id: {message['job_id']}"
                    raise IOError(e_msg)
        return result

    def health_check(self):
        self.health_sock.send(b'')
        return self.health_sock.recv() == b'OK'

    def close(self):
        self.health_sock.close()
        self.sub_sock.close()
        self.get_sock.close()
        self.context.term()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
