# Language capabilities

| Capability | Python | Swift | Kotlin/JVM | R |
| --- | --- | --- | --- | --- |
| WorkoutIntent decode + validation | full | full | full | full |
| Intent resolution (policies/defaults/status) | full | partial/native | partial/native | partial/native |
| TARGET merge/relational validation | full | not-supported | not-supported | not-supported |
| TrainingProfile/history integration | full | not-supported | not-supported | not-supported |
| Plan generation from intent | full | not-supported | not-supported | not-supported |
| Plan evaluation | full | read-only coverage | read-only ACTUAL | read-only ACTUAL |

Swift, Kotlin, and R resolution models are offline and do not invoke Python or
network services. “Partial” records that the current native resolver exposes
the stable result shape and core policy/status semantics but does not yet
implement every DB-aware validation, TARGET merge, profile/history path, or
native planner. Those gaps are explicitly scheduled for the v1.12 package goal.

Cross-language intent fixtures are parity inputs for later work; this release does not claim implementation parity.

The fixture oracle is `fixtures/cross-language/intent/`. Each case contains
structured inputs, canonical expected resolution (and flagship generation),
and metadata recording policy and artifact versions. v1.11 may consume these
fixtures; it does not begin that parity implementation here.
