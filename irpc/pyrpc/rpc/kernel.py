import zmq

from rpc.serializers import (send_msgpack, send_json, send_pickle,
                             receive_msgpack, receive_json, receive_pickle)


class Kernel():

    def __init__(self, context=None, health_port='5566',
                 submit_task_port='5567', get_task_port='5568',
                 serializer='pickle'):
        self.context = context or zmq.Context()
        self.set_sockets(health_port, submit_task_port, get_task_port)
        serializers = {
            'json': (receive_json, send_json),
            'msgpack': (receive_msgpack, send_msgpack),
            'pickle': (receive_pickle, send_pickle),
        }

        self.receive_func, self.send_func = serializers[serializer]

        self.handlers = {}

    def set_sockets(self, health_port, submit_task_port, get_task_port):
        self.health = self.context.socket(zmq.REP)
        self.health.bind(f"tcp://*:{health_port}")

        self.submits_task = self.context.socket(zmq.REP)
        self.submits_task.bind(f"tcp://*:{submit_task_port}")

        self.gets_task = self.context.socket(zmq.REQ)
        self.gets_task.connect(f"tcp://localhost:{get_task_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.health, zmq.POLLIN)
        self.poller.register(self.submits_task, zmq.POLLIN)

    def run(self):
        try:
            self._run()
        except KeyboardInterrupt:
            print("W: interrupt received, stopping...")
        finally:
            self._close()

    def _run(self):
        while True:
            socks = dict(self.poller.poll())
            if self.health in socks:
                self.health.recv()
                self.health.send(b'OK')
            if self.submits_task in socks:
                message = self.receive_func(self.submits_task)
                self.submits_task.send(b'OK')
                self.handler(message)

    def _close(self):
        socks = [self.health, self.submits_task, self.gets_task]
        [sock.close() for sock in socks if sock is not None]
        if self.context is not None:
            self.context.term()

    def handler(self, message):
        out = {'task_id': message['task_id'],
               'status': 'PENDING',
               'result': False}
        self.send_func(self.gets_task, out)
        assert self.gets_task.recv() == b'OK'
        try:
            if not message['endpoint'] in self.handlers:
                assert message['endpoint'] == 'endpoint not registered'
            result = self.handlers[message['endpoint']](*message['args'],
                                                        **message['kwargs'])
            status = 'SUCCESS'
            out = {'task_id': message['task_id'],
                   'status': status,
                   'result': result}
        except Exception as e:
            out = {'task_id': message['task_id'],
                   'status': 'FAILURE',
                   'error_type': e.__class__.__name__,
                   'error_msg': str(e)}
        self.send_func(self.gets_task, out)
        assert self.gets_task.recv() == b'OK'

    def register_handlers(self, new_handlers):
        for name, func in new_handlers.items():
            self.handlers[name] = func
