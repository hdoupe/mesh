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

int makeparams(struct params *input, const char * const params)
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

int main (void){
    char *teststring = "{\"mtr_wrt_group\": \"full\", \"file_name\": \"taxsimrun.txt\"}";
    struct params input;
    int status = makeparams (&input, teststring);
    assert (status==0);
    printf("received data: %s %s\n", input.mtr_wrt_group, input.file_name);
}
