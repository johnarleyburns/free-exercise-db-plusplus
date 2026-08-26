# Language capabilities

| Capability | Python | Swift | Kotlin/JVM | R |
| --- | --- | --- | --- | --- |
| WorkoutIntent decode + validation | full | native | native | native |
| Intent resolution (policies/defaults/status) | full | native core | native core | native core |
| TARGET merge/relational validation | full | native helpers + resolver | native helpers + resolver | native helpers + resolver |
| TrainingProfile/history integration | full | profile JSON input; native history deferred | profile JSON input; native history deferred | profile input; native history deferred |
| Plan generation from intent | full | not-supported | not-supported | not-supported |
| Plan evaluation | full | read-only coverage | read-only ACTUAL | read-only ACTUAL |

Swift, Kotlin, and R resolution models are offline and do not invoke Python or
network services. Native core resolution includes policy defaults, weekday
mapping, deterministic equipment overrides, profile equipment precedence,
partial TARGET merge/validation, stable provenance, and structured conflicts.
History-to-TrainingState derivation and native plan generation remain deferred
to v1.12 and are intentionally not represented as completed capabilities.

All non-history canonical resolution fixtures are executed by Python, Swift,
Kotlin/JVM, and R. The history fixture remains Python-only until the native
TrainingState derivation is implemented.

The fixture oracle is `fixtures/cross-language/intent/`. Python and Swift
execute the canonical non-history resolution matrix locally; Kotlin and R
have flagship/native consumer coverage. The history fixture remains Python-only
until native TrainingState derivation is implemented.
