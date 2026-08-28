# Language capabilities

v1.11 completed the Python reference engine and full Swift semantic engine
parity. v1.12 completed the Swift SPM application-grade API and packaging
hardening. v1.13 completed the native Kotlin/JVM engine port. v1.14 completes
the native R research/analysis engine. v1.15 adds a shared application
integration contract over all four engines.

| Capability | Python | Swift | Kotlin/JVM | R |
| --- | --- | --- | --- | --- |
| WorkoutIntent decode + validation | full | full native | full native | full native |
| Intent resolution (policies/defaults/status) | full | full native | full native | full native |
| TARGET merge/relational validation | full | full native | full native | full native |
| TrainingProfile/history integration | full | full native, adherence-rich | full native, adherence-rich | full native, research views |
| Plan generation from intent | full | full native production generator | full native production generator | full native deterministic generator |
| Plan evaluation | full | full native | full native | full native |
| Progression and CoachDecision | full | full native | full native | full native |
| Adaptive coaching | full | full native | full native | full native |
| Application request/result facade | full | full typed | full typed | full named-list |

Python, Swift, Kotlin, and R are offline and do not invoke network services or an
LLM. Swift, Kotlin, and R include policy defaults, weekday mapping, deterministic equipment
overrides, profile equipment precedence, partial TARGET merge/validation,
stable provenance, structured conflicts, full history/state semantics,
production generation, progression, and adaptive coaching.

Canonical Python-authored evaluation, history, progression, generation, and
adaptation fixtures are consumed by all four implementations under the shared
comparison policy. Native timestamp comparisons are offset-aware and exclude
future observations.

The fixture oracle is `fixtures/cross-language/`; Python remains the semantic
oracle. Swift, Kotlin, and R consume the same canonical fixtures.
