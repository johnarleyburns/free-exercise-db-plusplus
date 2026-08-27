# Language capabilities

| Capability | Python | Swift | Kotlin/JVM | R |
| --- | --- | --- | --- | --- |
| WorkoutIntent decode + validation | full | full native | partial legacy/current | partial legacy/current |
| Intent resolution (policies/defaults/status) | full | full native | partial legacy/current | partial legacy/current |
| TARGET merge/relational validation | full | full native | partial legacy/current | partial legacy/current |
| TrainingProfile/history integration | full | full native, adherence-rich | partial legacy/current | partial legacy/current |
| Plan generation from intent | full | full native production generator | deferred to v1.13 | deferred to v1.14 |
| Plan evaluation | full | full native | deferred to v1.13 | deferred to v1.14 |
| Progression and CoachDecision | full | full native | deferred to v1.13 | deferred to v1.14 |
| Adaptive coaching | full | full native | deferred to v1.13 | deferred to v1.14 |

Swift is offline and does not invoke Python, network services, or an LLM.
Swift includes policy defaults, weekday mapping, deterministic equipment
overrides, profile equipment precedence, partial TARGET merge/validation,
stable provenance, structured conflicts, full history/state semantics,
production generation, progression, and adaptive coaching. Kotlin and R
remain supported at their existing partial boundaries and are intentionally
deferred to v1.13 and v1.14 respectively.

Canonical Python-authored evaluation, history, progression, generation, and
adaptation fixtures are consumed by Swift under the shared comparison policy.
Native timestamp comparisons are offset-aware and exclude future observations.

The fixture oracle is `fixtures/cross-language/`; Python remains the semantic
oracle. Kotlin and R are not v1.11 parity deliverables.
