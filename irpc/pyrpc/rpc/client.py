import uuid

import zmq

from rpc.serializers import (send_msgpack, send_json, send_pickle,
                             receive_msgpack, receive_json, receive_pickle)


class Client():

    def __init__(self, kernel_id, context=None, health_port=None,
                 submit_task_port=None, get_task_port=None,
                 serializer='pickle'):
        self.context = context or zmq.Context()
        self.set_sockets(kernel_id, health_port, submit_task_port,
                         get_task_port)
        serializers = {
            'json': (receive_json, send_json),
            'msgpack': (receive_msgpack, send_msgpack),
            'pickle': (receive_pickle, send_pickle),
        }

        self.receive_func, self.send_func = serializers[serializer]

    def set_sockets(self, kernel_id, health_port, submit_task_port,
                    get_task_port):
        if health_port is None:
            info = self.context.socket(zmq.REQ)
            info.connect("tcp://127.0.0.1:8080")
            send_json(info, {'handle': 'info', 'kernel_id': kernel_id})
            r = receive_json(info)
            (health_port, submit_task_port,
                get_task_port) = (r['health_port'], r['submit_task_port'],
                                 r['get_task_port'])
            info.close()

        self.health_sock = self.context.socket(zmq.REQ)
        self.health_sock.connect(f"tcp://127.0.0.1:{health_port}")

        self.sub_sock = self.context.socket(zmq.REQ)
        self.sub_sock.connect(f"tcp://127.0.0.1:{submit_task_port}")

        self.get_sock = self.context.socket(zmq.REP)
        self.get_sock.bind(f"tcp://*:{get_task_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.get_sock)

        assert self.health_check()

    def submit(self, endpoint, args=(), kwargs={}):
        task_id = str(uuid.uuid4())
        data = {'task_id': task_id,
                'endpoint': endpoint,
                'args': args,
                'kwargs': kwargs}
        # print('submitting data', data)
        self.send_func(self.sub_sock, data)
        assert self.sub_sock.recv() == b'OK'
        return {'task_id': task_id, 'status': 'PENDING', 'result': None}

    def get(self, task):
        message = None
        while task['status'] == 'PENDING':
            socks = dict(self.poller.poll())
            if self.get_sock in socks:
                message = self.receive_func(self.get_sock)
                print(f"received message {message['task_id']}: {message['status']}")
                self.get_sock.send(b'OK')
                if message['task_id'] == task['task_id']:
                    task['status'] = message['status']
                    task['result'] = message['result']
                else:
                    e_msg = f"received unexpected task id: {message['task_id']}"
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
