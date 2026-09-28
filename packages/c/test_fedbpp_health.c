#include "fedbpp_health.h"

#include <string.h>

int main(void) {
    fedbpp_health_target target;
    char *copy = NULL;
    size_t length = 0;
    const char *json = "{\"schemaVersion\":\"0.3.0\",\"sessionId\":\"c\"}";
    if (fedbpp_health_target_from_string("fit", &target) != 0) return 1;
    if (target != FEDBPP_HEALTH_GARMIN_FIT) return 2;
    if (fedbpp_health_copy_sidecar("healthkit", json, strlen(json), &copy, &length) != 0) return 3;
    if (length != strlen(json) || memcmp(copy, json, length) != 0) return 4;
    fedbpp_health_free(copy);
    return 0;
}
