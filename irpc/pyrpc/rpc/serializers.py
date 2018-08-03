import msgpack
import json
import pickle


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


def send_pickle(socket, obj, flags=0):
    pickled = pickle.dumps(obj)
    return socket.send(pickled, flags=flags)


def receive_pickle(socket, flags=0):
    received = socket.recv(flags)
    return pickle.loads(received)
