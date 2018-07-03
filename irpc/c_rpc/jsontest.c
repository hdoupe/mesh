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

struct params makeparams(const char * const params)
{
    struct params input;
    cJSON *json_obj = cJSON_Parse(params);
    if (json_obj == NULL)
    {
        const char *error_ptr = cJSON_GetErrorPtr();
        if (error_ptr != NULL)
        {
            fprintf(stderr, "Error before: %s\n", error_ptr);
        }
        cJSON_Delete(json_obj);
        return input;
    }

    cJSON *mtr_wrt_group = cJSON_GetObjectItemCaseSensitive(json_obj, "mtr_wrt_group");
    cJSON *file_name = cJSON_GetObjectItemCaseSensitive(json_obj, "file_name");

    // we are expecting strings
    // TODO: figure out better return type
    if (!cJSON_IsString(mtr_wrt_group) || !cJSON_IsString(file_name)) {
        printf("\"mtr_wrt_group\" and \"file_name\" should be strings\n");
        cJSON_Delete(json_obj);
        return input;
    }

    // allocate memory to struct fields and copy data to them
    input.mtr_wrt_group = malloc(strlen(mtr_wrt_group->valuestring) + 1);
    input.file_name = malloc(strlen(file_name->valuestring) + 1);
    strcpy(input.mtr_wrt_group, mtr_wrt_group->valuestring);
    strcpy(input.file_name, file_name->valuestring);

    printf("received data: %s %s\n", input.mtr_wrt_group, input.file_name);

    cJSON_Delete(json_obj);
    return input;
}

int main (void){
    // char *teststring = "{\"name\": \"Awesome 4K\", \"resolutions\": [{\"width\": 1280, \"height\": 720}, {\"width\": 1920, \"height\": 1080}, {\"width\": 3840, \"height\": 2160}]}";
    char *teststring = "{\"mtr_wrt_group\": \"full\", \"file_name\": \"taxsimrun.txt\"}";
    struct params input;
    input = makeparams (teststring);
    printf("received data: %s %s\n", input.mtr_wrt_group, input.file_name);
}
