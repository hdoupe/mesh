//  Hello World server

#include <zmq.h>
#include <stdio.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>

//  Convert C string to 0MQ string and send to socket
static int
s_send (void *socket, char *string) {
    int size = zmq_send (socket, string, strlen (string), 0);
    return size;
}


//  Receive ZeroMQ string from socket and convert into C string
//  Chops string at 255 chars, if it's longer
static char *
s_recv (void *socket) {
    char buffer [256];
    int size = zmq_recv (socket, buffer, 255, 0);
    if (size == -1)
        return NULL;
    if (size > 255)
        size = 255;
    buffer [size] = 0;
    return strdup (buffer);
}


int main (void)
{
    //  Socket to talk to clients
    void *context = zmq_ctx_new ();

    void *health = zmq_socket (context, ZMQ_REP);
    int rc = zmq_bind (health, "tcp://*:5566");
    assert (rc == 0);

    void *worker_rep = zmq_socket (context, ZMQ_REP);
    rc = zmq_bind (worker_rep, "tcp://*:5567");
    assert (rc == 0);

    void *worker_req = zmq_socket (context, ZMQ_REQ);
    zmq_connect (worker_req, "tcp://localhost:5568");

    while (1) {
        char msg [256];
        // polling http://zguide.zeromq.org/page:all#Handling-Multiple-Sockets
        zmq_pollitem_t items [] = {
            { health, 0, ZMQ_POLLIN, 0 },
            { worker_rep, 0, ZMQ_POLLIN, 0 },
        };
        zmq_poll (items, 2, -1);
        if (items[0].revents & ZMQ_POLLIN) {
            int size = zmq_recv (health, msg, 255, 0);
            if (size != -1) {
                s_send (health, "OK");
            }
        }
        if (items[1].revents & ZMQ_POLLIN) {
            int size = zmq_recv (worker_rep, msg, 255, 0);
            if (size != -1) {
                s_send (worker_rep, "OK");
            }
        }
    }
    zmq_close (worker_rep);
    zmq_close (worker_req);
    zmq_ctx_destroy (context);
    return 0;
}
