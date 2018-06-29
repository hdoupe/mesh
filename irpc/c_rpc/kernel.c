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

int main (void)
{
    //  Socket to talk to clients
    printf("setting up sockets...\n");
    void *context = zmq_ctx_new ();
    void *worker_rep = zmq_socket (context, ZMQ_REP);
    int rc = zmq_bind (worker_rep, "tcp://*:5566");
    assert (rc == 0);

    void *worker_req = zmq_socket (context, ZMQ_REQ);
    rc = zmq_bind (worker_req, "tcp://*:5567");
    assert (rc == 0);
    printf("listening...\n");
    while (1) {
        char msg [256];
        // polling http://zguide.zeromq.org/page:all#Handling-Multiple-Sockets
        zmq_pollitem_t items [] = {
            { worker_rep, 0, ZMQ_POLLIN, 0 },
        };
        zmq_poll (items, 1, -1);
        if (items[0].revents & ZMQ_POLLIN) {
            int size = zmq_recv (worker_rep, msg, 255, 0);
            if (size != -1) {
                printf("msg: got message\n");
                s_send (worker_rep, "back at you");
            }
        }
    }
    zmq_close (worker_rep);
    zmq_close (worker_req);
    zmq_ctx_destroy (context);
    return 0;
}
