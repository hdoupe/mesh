//  Hello World server

#include <zmq.h>
#include <cjson/cJSON.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <assert.h>


struct message {
    char *job_id;
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
extern void runmodel(char *, int, char *, int, char *, int, char *, int);

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
    // host.docker.internal is necessary for macs
    // this should be changed to localhost to be more portable
    zmq_connect (worker_req, "tcp://host.docker.internal:5568");
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
                handler (msg, worker_req);
            }
        }
    }
    zmq_close (health);
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

int handler (char *msg, void* socket) {
    struct message m;
    parse_status(&m, msg);
    if (strcmp(m.endpoint, "taxsim") == 0) {
        int status = taxsimrun(m.job_id, m.params_str, socket);
        return status;
    } else {
        char *error_msg;
        json_status (&error_msg, m.job_id, "FAILURE", "Endpoint doesn\'t exist");
        s_send(socket, error_msg);
        free (error_msg);
        return 1;
    }
    return 0;
}

int taxsimrun(char* job_id, char *msg, void* socket){
    char *pending;
    json_status (&pending, job_id, "PENDING", "");
    s_send(socket, pending);
    free (pending);
    printf("received: %s\n", s_recv(socket));

    struct params input;
    int status = parse_taxsim_params (&input, msg);
    if (status != 0) {
        printf("Bad JSON input: %s\n", msg);
        char *error_msg;
        json_status (&error_msg, job_id, "FAILURE", "Failed to allocate sufficient memory");
        s_send(socket, error_msg);
        free (error_msg);
        return 1;
    }
    char *mname = "out.msg";
    int fnamesize = strlen(input.file_name) + 1;
    int argsize = strlen(input.mtr_wrt_group) + 1;
    int mnamesize = strlen(mname) + 1;
    // allocate all memory up front. it would be better do this dynamically
    int buffersize = 60000000;
    char *buffer;
    buffer = (char*) malloc(sizeof(char)*buffersize);
    if (buffer == NULL){
        char *error_msg;
        json_status (&error_msg, job_id, "FAILURE", "Failed to allocate sufficient memory");
        s_send(socket, error_msg);
        free (error_msg);
        return 1;
    }
    printf("%s %s %s\n", input.file_name, input.mtr_wrt_group, mname);

    runmodel(input.file_name, fnamesize, mname, mnamesize, input.mtr_wrt_group,
             argsize, buffer, buffersize);

    char *json_str;
    if (json_status (&json_str, job_id, "SUCCESS", buffer) == 1){
        char *error_msg;
        json_status (&error_msg, job_id, "FAILURE", "Bad JSON");
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
    printf("parsing message: %s\n", m_str);
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
    cJSON *job_id = cJSON_GetObjectItemCaseSensitive (json_obj, "job_id");
    cJSON *endpoint = cJSON_GetObjectItemCaseSensitive (json_obj, "endpoint");
    cJSON *params_str = cJSON_GetObjectItemCaseSensitive (json_obj, "args");
    char *tmpparam = cJSON_Print (params_str);

    m->job_id = malloc (strlen (job_id->valuestring) + 1);
    m->endpoint = malloc (strlen (endpoint->valuestring) + 1);
    m->params_str = malloc (strlen (tmpparam) + 1);
    strcpy (m->job_id, job_id->valuestring);
    strcpy (m->endpoint, endpoint->valuestring);
    strcpy (m->params_str, tmpparam);

    printf("params_str: %s\n", m->params_str);

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

int json_status(char **json_str, char *job_id, char *status, char *result){
    cJSON *res = cJSON_CreateObject();
    if (cJSON_AddStringToObject(res, "job_id", job_id) == NULL){
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
