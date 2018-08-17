import uuid

import zmq

from rpc.serializers import (send_msgpack, send_json, send_pickle,
                             receive_msgpack, receive_json, receive_pickle)
from dataclasses import dataclass, field
from typing import Union, Iterable, Dict, Any


class TaskResultNotReady(Exception):
    pass


class TaskFailure(Exception):
    pass


@dataclass
class Task:
    client: 'Client'
    task_id: str = field(init=False,
                         default_factory=lambda: str(uuid.uuid1()))
    endpoint: str
    args: Iterable[Any] = ()
    kwargs: Dict[str, Any] = field(default_factory=dict)
    verbose: bool = False
    status: str = field(default=None, init=False)
    _result: Union[str, None] = field(default=None, init=False)
    _error_msg: Union[str, None] = field(default=None, init=False)
    _error_type: Union[str, None] = field(default=None, init=False)

    @property
    def result(self):
        if self.status == 'SUCCESS':
            return self._result
        elif self.status == 'PENDING':
            raise TaskResultNotReady()
        elif self.status == 'FAILURE':
            raise TaskFailure(self._error_type, self._error_msg)
        else:
            raise RuntimeError('Unknown status: ', self.status)

    def submit(self):
        data = {'task_id': self.task_id,
                'endpoint': self.endpoint,
                'args': self.args,
                'kwargs': self.kwargs}
        if self.verbose:
            print('submitting data', data)
        self.client.send_func(self.client.sub_sock, data)
        assert self.client.sub_sock.recv() == b'OK'
        self.status = 'PENDING'

    def get(self):
        message = None
        while self.status == 'PENDING':
            socks = dict(self.client.poller.poll())
            if self.client.get_sock in socks:
                message = self.client.receive_func(self.client.get_sock)
                if self.verbose:
                    print(f"received message {message['task_id']}: " +
                          f"{message['status']}")
                self.client.get_sock.send(b'OK')
                if message['task_id'] == self.task_id:
                    self.status = message['status']
                    if message['status'] == 'SUCCESS':
                        self._result = message['result']
                    elif self.status == 'FAILURE':
                        self._error_msg = message['error_msg']
                        self._error_type = message['error_type']
                else:
                    e_msg = ("received unexpected task id: " +
                             f"{message['task_id']}")
                    raise IOError(e_msg)
        return self.result


class Client:
    def __init__(self, kernel_id, context=None, health_port=None,
                 submit_task_port=None, get_task_port=None,
                 serializer='pickle', verbose=False):
        self.context = context or zmq.Context()
        self.set_sockets(kernel_id, health_port, submit_task_port,
                         get_task_port)
        serializers = {
            'json': (receive_json, send_json),
            'msgpack': (receive_msgpack, send_msgpack),
            'pickle': (receive_pickle, send_pickle),
        }

        self.receive_func, self.send_func = serializers[serializer]

        self.verbose = verbose

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

    def do_task(self, endpoint, args=(), kwargs={}):
        t = Task(self, endpoint, args, kwargs, verbose=self.verbose)
        t.submit()
        return t.get()

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
