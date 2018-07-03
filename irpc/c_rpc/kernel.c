//  Hello World server

#include <zmq.h>
#include <cjson/cJSON.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>


struct params {
    char *mtr_wrt_group;
    char *file_name;
};

static int s_send (void *socket, char *string);
static char *s_recv (void *socket);
int parse_params(struct params *input, const char * const params);


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
        char *msg;
        // polling http://zguide.zeromq.org/page:all#Handling-Multiple-Sockets
        zmq_pollitem_t items [] = {
            { health, 0, ZMQ_POLLIN, 0 },
            { worker_rep, 0, ZMQ_POLLIN, 0 },
        };
        zmq_poll (items, 2, -1);
        if (items[0].revents & ZMQ_POLLIN) {
            msg = s_recv (health);
            if (msg) {
                s_send(health, "OK");
            }
        }
        if (items[1].revents & ZMQ_POLLIN) {
            msg = s_recv (worker_rep);
            if (msg) {
                s_send (worker_rep, "OK");
                struct params input;
                int status = parse_params (&input, msg);
                if (status != 0) {
                    printf("Bad JSON input: %s\n", msg);
                } else {
                    printf("doing work... %s %s\n", input.mtr_wrt_group, input.file_name);
                }
            }
        }
    }
    zmq_close (worker_rep);
    zmq_close (worker_req);
    zmq_ctx_destroy (context);
    return 0;
}

// see https://github.com/booksbyus/zguide/blob/master/examples/C/zhelpers.h
// TODO: do formal link i.e. #include <zhelpers.h>
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


int parse_params(struct params *input, const char * const params)
{
    cJSON *json_obj = cJSON_Parse(params);
    if (json_obj == NULL)
    {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr != NULL)
        {
            fprintf(stderr, "Error before: %s\n", error_ptr);
        }
        cJSON_Delete(json_obj);
        return 1;
    }

    cJSON *mtr_wrt_group = cJSON_GetObjectItemCaseSensitive(json_obj, "mtr_wrt_group");
    cJSON *file_name = cJSON_GetObjectItemCaseSensitive(json_obj, "file_name");

    // we are expecting strings
    if (!cJSON_IsString(mtr_wrt_group) || !cJSON_IsString(file_name)) {
        printf("\"mtr_wrt_group\" and \"file_name\" should be strings\n");
        cJSON_Delete(json_obj);
        return 1;
    }

    // allocate memory to struct fields and copy data to them
    input->mtr_wrt_group = malloc(strlen(mtr_wrt_group->valuestring) + 1);
    input->file_name = malloc(strlen(file_name->valuestring) + 1);
    strcpy(input->mtr_wrt_group, mtr_wrt_group->valuestring);
    strcpy(input->file_name, file_name->valuestring);

    cJSON_Delete(json_obj);
    return 0;
}
