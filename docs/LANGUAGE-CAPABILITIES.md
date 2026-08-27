# Language capabilities

| Capability | Python | Swift | Kotlin/JVM | R |
| --- | --- | --- | --- | --- |
| WorkoutIntent decode + validation | full | native | native | native |
| Intent resolution (policies/defaults/status) | full | native core | native core | native core |
| TARGET merge/relational validation | full | native helpers + resolver | native helpers + resolver | native helpers + resolver |
| TrainingProfile/history integration | full | profile JSON input; deterministic native state projection | profile JSON input; deterministic native state projection | profile input; deterministic native state projection |
| Plan generation from intent | full | native deterministic draft | native deterministic draft | native deterministic draft |
| Plan evaluation | full | read-only coverage | read-only ACTUAL | read-only ACTUAL |

Swift, Kotlin, and R resolution models are offline and do not invoke Python or
network services. Native core resolution includes policy defaults, weekday
mapping, deterministic equipment overrides, profile equipment precedence,
partial TARGET merge/validation, stable provenance, and structured conflicts.
History-to-TrainingState derivation and native plan generation remain deferred
to v1.12 and are intentionally not represented as completed capabilities.

All non-history canonical resolution fixtures are executed by Python, Swift,
Kotlin/JVM, and R. History-aware resolution now adds a deterministic native
TrainingState projection when history and `asOf` are supplied, including the
bounded 28-day window, active-plan identity/cycle position, and aggregated
exercise counts. The full Python adherence analysis remains richer than this
portable projection.

The fixture oracle is `fixtures/cross-language/intent/`. Python, Swift,
Kotlin/JVM, and R execute the canonical non-history resolution matrix; the
history fixture and flagship draft are exercised by native package tests and
isolated consumers. Full adherence-rich TrainingState and production plan
optimization remain v1.12 work.
