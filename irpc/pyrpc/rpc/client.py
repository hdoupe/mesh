import uuid

import zmq

from rpc.serializers import (send_msgpack, send_json, send_pickle,
                             receive_msgpack, receive_json, receive_pickle)


class Client():

    def __init__(self, context=None, health_port='5566',
                 submit_job_port='5567', get_job_port='5568',
                 serializer='pickle'):
        self.context = context or zmq.Context()
        self.set_sockets(health_port, submit_job_port, get_job_port)
        serializers = {
            'json': (receive_json, send_json),
            'msgpack': (receive_msgpack, send_msgpack),
            'pickle': (receive_pickle, send_pickle),
        }

        self.receive_func, self.send_func = serializers[serializer]

    def set_sockets(self, health_port, submit_job_port, get_job_port):
        self.health_sock = self.context.socket(zmq.REQ)
        self.health_sock.connect(f"tcp://127.0.0.1:{health_port}")

        self.sub_sock = self.context.socket(zmq.REQ)
        self.sub_sock.connect(f"tcp://127.0.0.1:{submit_job_port}")

        self.get_sock = self.context.socket(zmq.REP)
        self.get_sock.bind(f"tcp://*:{get_job_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.get_sock)

        assert self.health_check()

    def submit(self, endpoint, args=(), kwargs={}):
        job_id = str(uuid.uuid4())
        data = {'job_id': job_id,
                'endpoint': endpoint,
                'args': args,
                'kwargs': kwargs}
        # print('submitting data', data)
        self.send_func(self.sub_sock, data)
        assert self.sub_sock.recv() == b'OK'
        return {'job_id': job_id, 'status': 'PENDING', 'result': None}

    def get(self, task):
        message = None
        while task['status'] == 'PENDING':
            socks = dict(self.poller.poll())
            if self.get_sock in socks:
                message = self.receive_func(self.get_sock)
                print(f"received message {message['job_id']}: {message['status']}")
                self.get_sock.send(b'OK')
                if message['job_id'] == task['job_id']:
                    task['status'] = message['status']
                    task['result'] = message['result']
                else:
                    e_msg = f"received unexpected job id: {message['job_id']}"
                    raise IOError(e_msg)
        return task

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
