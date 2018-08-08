import zmq

from rpc.serializers import (send_msgpack, send_json, send_pickle,
                             receive_msgpack, receive_json, receive_pickle)


class Kernel():

    def __init__(self, context=None, health_port='5566', rep_port='5567',
                 req_port='5568', serializer='pickle'):
        self.context = context or zmq.Context()
        self.set_sockets(health_port, rep_port, req_port)
        serializers = {
            'json': (receive_json, send_json),
            'msgpack': (receive_msgpack, send_msgpack),
            'pickle': (receive_pickle, send_pickle),
        }

        self.receive_func, self.send_func = serializers[serializer]

        self.handlers = {}

    def set_sockets(self, health_port, rep_port, req_port):
        print('got ports', health_port, rep_port, req_port)
        self.health = self.context.socket(zmq.REP)
        self.health.bind(f"tcp://*:{health_port}")

        self.worker_rep = self.context.socket(zmq.REP)
        self.worker_rep.bind(f"tcp://*:{rep_port}")

        self.worker_req = self.context.socket(zmq.REQ)
        self.worker_req.connect(f"tcp://localhost:{req_port}")

        self.poller = zmq.Poller()
        self.poller.register(self.health, zmq.POLLIN)
        self.poller.register(self.worker_rep, zmq.POLLIN)

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
            if self.worker_rep in socks:
                message = self.receive_func(self.worker_rep)
                self.worker_rep.send(b'OK')
                self.handler(message)

    def _close(self):
        socks = [self.health, self.worker_req, self.worker_rep]
        [sock.close() for sock in socks if sock is not None]
        if self.context is not None:
            self.context.term()

    def handler(self, message):
        out = {'job_id': message['job_id'],
               'status': 'PENDING',
               'result': False}
        self.send_func(self.worker_req, out)
        assert self.worker_req.recv() == b'OK'
        try:
            if not message['endpoint'] in self.handlers:
                assert message['endpoint'] == 'endpoint not registered'
            result = self.handlers[message['endpoint']](*message['args'])
            status = 'SUCCESS'
        except Exception as e:
            result = e.__str__()
            status = 'FAILURE'
        out = {'job_id': message['job_id'], 'status': status, 'result': result}
        self.send_func(self.worker_req, out)
        assert self.worker_req.recv() == b'OK'

    def register_handlers(self, new_handlers):
        for name, func in new_handlers.items():
            self.handlers[name] = func
