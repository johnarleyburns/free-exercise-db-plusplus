# Language capabilities

v1.11 completed the Python reference engine and full Swift semantic engine
parity. v1.12 completed the Swift SPM application-grade API and packaging
hardening. v1.13 completes the native Kotlin/JVM engine port. R remains the
v1.14 full-engine/research port.

| Capability | Python | Swift | Kotlin/JVM | R |
| --- | --- | --- | --- | --- |
| WorkoutIntent decode + validation | full | full native | full native | partial/research |
| Intent resolution (policies/defaults/status) | full | full native | full native | partial/research |
| TARGET merge/relational validation | full | full native | full native | partial/research |
| TrainingProfile/history integration | full | full native, adherence-rich | full native, adherence-rich | partial/research |
| Plan generation from intent | full | full native production generator | full native production generator | partial/research |
| Plan evaluation | full | full native | full native | partial/research |
| Progression and CoachDecision | full | full native | full native | partial/research |
| Adaptive coaching | full | full native | full native | partial/research |

Python, Swift, and Kotlin are offline and do not invoke network services or an
LLM. Swift and Kotlin include policy defaults, weekday mapping, deterministic equipment
overrides, profile equipment precedence, partial TARGET merge/validation,
stable provenance, structured conflicts, full history/state semantics,
production generation, progression, and adaptive coaching. Kotlin and R
R remains at its partial research boundary; its full port is intentionally
deferred to v1.14.

Canonical Python-authored evaluation, history, progression, generation, and
adaptation fixtures are consumed by Swift under the shared comparison policy.
Native timestamp comparisons are offset-aware and exclude future observations.

The fixture oracle is `fixtures/cross-language/`; Python remains the semantic
oracle. Kotlin consumes the same canonical fixtures; R is not a v1.13 parity
deliverable.
