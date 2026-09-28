#include "fedbpp_health.h"

#include <stdlib.h>
#include <string.h>

static int target_for(const char *name, fedbpp_health_target *out) {
    if (!name || !out) return 0;
    if (strcmp(name, "garmin-fit") == 0 || strcmp(name, "garmin") == 0 || strcmp(name, "fit") == 0) {
        *out = FEDBPP_HEALTH_GARMIN_FIT; return 1;
    }
    if (strcmp(name, "healthkit") == 0) { *out = FEDBPP_HEALTHKIT; return 1; }
    if (strcmp(name, "health-connect") == 0 || strcmp(name, "health_connect") == 0 || strcmp(name, "healthconnect") == 0) {
        *out = FEDBPP_HEALTH_CONNECT; return 1;
    }
    return 0;
}

int fedbpp_health_target_from_string(const char *name, fedbpp_health_target *out) {
    return target_for(name, out) ? 0 : 1;
}

int fedbpp_health_copy_sidecar(const char *target, const char *canonical_json,
                               size_t canonical_length, char **out_json,
                               size_t *out_length) {
    fedbpp_health_target parsed;
    if (!target_for(target, &parsed) || !canonical_json || !out_json || !out_length) return 1;
    char *copy = (char *)malloc(canonical_length + 1u);
    if (!copy) return 2;
    memcpy(copy, canonical_json, canonical_length);
    copy[canonical_length] = '\0';
    *out_json = copy;
    *out_length = canonical_length;
    return 0;
}

void fedbpp_health_free(void *memory) { free(memory); }
