import msgpack
import json


def send_msgpack(socket, obj, flags=0):
    packed = msgpack.dumps(obj, use_bin_type=True)
    return socket.send(packed, flags=flags)


def receive_msgpack(socket, flags=0):
    received = socket.recv(flags)
    return msgpack.loads(received, encoding='utf8', use_list=True)


def send_json(socket, obj, flags=0):
    serialized = json.dumps(obj).encode('utf-8')
    return socket.send(serialized, flags=flags)


def receive_json(socket, flags=0):
    received = socket.recv(flags)
    return json.loads(received.decode('utf-8'))
