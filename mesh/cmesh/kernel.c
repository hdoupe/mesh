//  Hello World server

#include <zmq.h>
#include <cjson/cJSON.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>


struct message {
    char *task_id;
    char *endpoint;
    char *params_str;
};

struct params {
    char *mtr_wrt_group;
    char *file_name;
};

static int s_send (void *socket, char *string);
static char *s_recv (void *socket);
int parse_status(struct message *m, const char * const m_str);
int json_status(char **, char *, char *, char *);
int taxsimrun(char *, char *, void *socket);
int parse_taxsim_params(struct params *input, const char * const params);
extern void runmodel(char *, int, char *, int, char *, int);

int main (void)
{
    //  Socket to talk to clients
    void *context = zmq_ctx_new ();

    void *health = zmq_socket (context, ZMQ_REP);
    int rc = zmq_bind (health, "tcp://*:5566");
    assert (rc == 0);

    void *submits_task = zmq_socket (context, ZMQ_REP);
    rc = zmq_bind (submits_task, "tcp://*:5567");
    assert (rc == 0);

    void *gets_task = zmq_socket (context, ZMQ_REQ);
    // host.docker.internal is necessary for macs
    // this should be changed to localhost to be more portable
    zmq_connect (gets_task, "tcp://host.docker.internal:5568");
    while (1) {
        char *msg;
        // polling http://zguide.zeromq.org/page:all#Handling-Multiple-Sockets
        zmq_pollitem_t items [] = {
            { health, 0, ZMQ_POLLIN, 0 },
            { submits_task, 0, ZMQ_POLLIN, 0 },
        };
        zmq_poll (items, 2, -1);
        if (items[0].revents & ZMQ_POLLIN) {
            msg = s_recv (health);
            if (msg) {
                s_send(health, "OK");
            }
        }
        if (items[1].revents & ZMQ_POLLIN) {
            msg = s_recv (submits_task);
            if (msg) {
                s_send (submits_task, "OK");
                handler (msg, gets_task);
            }
        }
        free(msg);
    }
    zmq_close (health);
    zmq_close (submits_task);
    zmq_close (gets_task);
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
    int buffersize = 40000000;
    char* buffer = malloc(sizeof(char) * buffersize);
    int size = zmq_recv (socket, buffer, buffersize, 0);
    if (size == -1)
        return NULL;
    if (size > buffersize)
        return NULL;
    buffer [size] = 0;
    char* bptr = strdup (buffer);
    free(buffer);
    return bptr;
}

int handler (char *msg, void* socket) {
    struct message m;
    parse_status(&m, msg);
    if (strcmp(m.endpoint, "taxsim") == 0) {
        int status = taxsimrun(m.task_id, m.params_str, socket);
        return status;
    } else {
        char *error_msg;
        json_status (&error_msg, m.task_id, "FAILURE", "Endpoint doesn\'t exist");
        s_send(socket, error_msg);
        free (error_msg);
        return 1;
    }
    return 0;
}

int taxsimrun(char* task_id, char *msg, void* socket){
    char *pending;
    json_status (&pending, task_id, "PENDING", "");
    s_send(socket, pending);
    free (pending);
    printf("received: %s\n", s_recv(socket));

    struct params input;
    int status = parse_taxsim_params (&input, msg);
    if (status != 0) {
        printf("Bad JSON input: %s\n", msg);
        char *error_msg;
        json_status (&error_msg, task_id, "FAILURE", "Failed to allocate sufficient memory");
        s_send(socket, error_msg);
        free (error_msg);
        return 1;
    }
    int fnamesize = strlen(input.file_name) + 1;
    int argsize = strlen(input.mtr_wrt_group) + 1;
    // allocate all memory up front. it would be better do this dynamically
    int buffersize = 60000000;
    char *buffer;
    buffer = (char*) malloc(sizeof(char)*buffersize);
    if (buffer == NULL){
        char *error_msg;
        json_status (&error_msg, task_id, "FAILURE", "Failed to allocate sufficient memory");
        s_send(socket, error_msg);
        free (error_msg);
        return 1;
    }

    runmodel(input.file_name, fnamesize, input.mtr_wrt_group,
             argsize, buffer, buffersize);

    char *json_str;
    if (json_status (&json_str, task_id, "SUCCESS", buffer) == 1){
        char *error_msg;
        json_status (&error_msg, task_id, "FAILURE", "Bad JSON");
        s_send (socket, error_msg);
        return 1;
    }
    s_send (socket, json_str);
    printf("received: %s\n", s_recv (socket));
    free(buffer);
    free(json_str);

    return 0;

}


int parse_status(struct message *m, const char * const m_str) {
    cJSON *json_obj = cJSON_Parse (m_str);
    if (json_obj == NULL)
    {
        printf("null json_obj\n");
        const char *error_ptr = cJSON_GetErrorPtr ();
        if (error_ptr != NULL)
        {
            fprintf(stderr, "Error before: %s\n", error_ptr);
        }
        cJSON_Delete (json_obj);
        return 1;
    }
    cJSON *task_id = cJSON_GetObjectItemCaseSensitive (json_obj, "task_id");
    cJSON *endpoint = cJSON_GetObjectItemCaseSensitive (json_obj, "endpoint");
    cJSON *params_str = cJSON_GetObjectItemCaseSensitive (json_obj, "args");
    char *tmpparam = cJSON_Print (params_str);

    m->task_id = malloc (strlen (task_id->valuestring) + 1);
    m->endpoint = malloc (strlen (endpoint->valuestring) + 1);
    m->params_str = malloc (strlen (tmpparam) + 1);
    strcpy (m->task_id, task_id->valuestring);
    strcpy (m->endpoint, endpoint->valuestring);
    strcpy (m->params_str, tmpparam);

    cJSON_Delete (json_obj);
    free (tmpparam);
    return 0;
}


int parse_taxsim_params(struct params *input, const char * const params)
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

    // allocate memory to struct fields and copy data to them
    input->mtr_wrt_group = malloc(strlen(mtr_wrt_group->valuestring) + 1);
    input->file_name = malloc(strlen(file_name->valuestring) + 1);
    strcpy(input->mtr_wrt_group, mtr_wrt_group->valuestring);
    strcpy(input->file_name, file_name->valuestring);

    cJSON_Delete(json_obj);
    return 0;
}

int json_status(char **json_str, char *task_id, char *status, char *result){
    cJSON *res = cJSON_CreateObject();
    if (cJSON_AddStringToObject(res, "task_id", task_id) == NULL){
        return 1;
    }
    if (cJSON_AddStringToObject(res, "status", status) == NULL){
        return 1;
    }
    if (cJSON_AddStringToObject(res, "result", result) == NULL){
        return 1;
    }
    char *json_str_tmp = cJSON_Print(res);
    *json_str = malloc(strlen(json_str_tmp) + 1);
    strcpy(*json_str, json_str_tmp);
    cJSON_Delete(res);
    free(json_str_tmp);
    return 0;
}
