#
#   Hello World client in Python
#   Connects REQ socket to tcp://localhost:5555
#   Sends "Hello" to server, expects "World" back
#

import zmq
import msgpack

context = zmq.Context()

#  Socket to talk to server
print("Connecting to hello world server…")
socket = context.socket(zmq.REQ)
socket.connect("tcp://localhost:5555")

requests = [{"endpoint": "individual", "contents": [2]},
            {"endpoint": "corporate", "contents": [3, 4]}]

#  Do 10 requests, waiting each time for a response
for request in requests:
    print("Sending request %s …" % request)
    socket.send(msgpack.packb(request))

    #  Get the reply.
    message = socket.recv()
    print("Received reply %s [ %s ]" % (request, msgpack.unpackb(message)))
