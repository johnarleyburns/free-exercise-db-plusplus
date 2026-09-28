#ifndef FEDBPP_HEALTH_H
#define FEDBPP_HEALTH_H

#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

typedef enum fedbpp_health_target {
    FEDBPP_HEALTH_GARMIN_FIT = 1,
    FEDBPP_HEALTHKIT = 2,
    FEDBPP_HEALTH_CONNECT = 3
} fedbpp_health_target;

/*
 * The C core is deliberately platform-neutral.  It owns the exact DB++
 * sidecar bytes; a Garmin C SDK, Objective-C HealthKit host, or Android JNI
 * host owns the native projection.  This keeps all DB++ health fields intact
 * without making the core depend on any mobile SDK or JSON library.
 */
int fedbpp_health_target_from_string(const char *name, fedbpp_health_target *out);

/* Make an owned byte-for-byte copy of a canonical DB++ ACTUAL JSON document. */
int fedbpp_health_copy_sidecar(const char *target, const char *canonical_json,
                               size_t canonical_length, char **out_json,
                               size_t *out_length);

void fedbpp_health_free(void *memory);

#ifdef __cplusplus
}
#endif

#endif
