# Application integration

Free Exercise DB++ is a deterministic, offline domain engine. The host
application owns natural-language parsing, UI, accounts, persistence, sync,
authorization, notifications, billing, and user approval. DB++ owns the
structured training domain: `WorkoutIntent`, `TrainingProfile`, `VolumeTarget`,
PLAN, ACTUAL, `TrainingHistory`, `TrainingState`, evaluation, progression, and
advisory adaptation. There is no LLM, network, or current-time dependency in
the semantic core.

## Request and result contract

`training-request.schema.json` and `training-result.schema.json` define the
transport-neutral application envelope. Both currently use independent schema
version `0.1.0`. Canonical domain documents remain nested domain documents;
the envelope does not introduce a second PLAN or ACTUAL representation.

The operation is always explicit:

```text
human / LLM / UI
        │
        ▼
WorkoutIntent → TrainingRequest → TrainingEngine
                                  /       |       \
                              clarify   plan     adapt
                                  \       |       /
                                   TrainingResult
                                         │
                                         ▼
                                   host application
```

Use `resolve_intent` when the host needs clarification, `generate_from_intent`
when the request should resolve and generate, `generate_plan` when profile and
target are already resolved, `evaluate_plan` for an existing PLAN,
`derive_state` for history analysis, `suggest_progression` for CoachDecision
documents, and `adapt_plan` for an advisory revision. DB++ never guesses
whether a request means a new plan or adaptation and never activates a
proposal.

```text
existing PLAN + ACTUAL history + TARGET + profile + explicit asOf
                              │
                              ▼
                    TrainingRequest(adapt_plan)
                              │
                              ▼
                       TrainingState
                              │
                              ▼
                     CoachDecision[]
                              │
                              ▼
                    proposed PLAN revision
```

The result envelope always contains `schemaVersion`, `requestId`, `operation`,
`status`, the applicable canonical result fields, structured issues, and
provenance. Normal domain outcomes are returned as statuses rather than
exceptions:

| Status | Host action |
| --- | --- |
| `resolved`, `resolved_with_defaults` | Continue with the resolution. |
| `needs_clarification` | Ask for the listed `missingInformation`. |
| `invalid`, `invalid_input` | Correct the request or show structured `issues`/`conflicts`. |
| `unsatisfiable` | Explain constraints/target gaps; do not activate a PLAN. |
| `generated`, `generated_with_target_gaps` | Review and store the returned PLAN and evaluation. |
| `evaluated` | Use the evaluation report. |
| `state_derived` | Store or analyze the returned TrainingState. |
| `progression_available`, `insufficient_data` | Review CoachDecision documents or collect more ACTUAL data. |
| `revision_proposed`, `no_change` | Present/store the advisory result; host approval is required before activation. |

Every request that depends on chronology supplies an offset-aware `asOf`.
Persist canonical JSON documents and retain their IDs, schema versions, and
provenance. Missing, null, zero, false, and empty collections remain distinct.

## Integration checklist for coding agents

1. Add the package dependency: [Swift](SWIFT-GETTING-STARTED.md),
   [Kotlin](KOTLIN-API.md), [Python](../packages/python/README.md), or
   [R](R-API.md).
2. Initialize the bundled offline engine.
3. Define persistence for canonical JSON PLAN, ACTUAL, TARGET, and history.
4. Convert user input into a structured `WorkoutIntent`.
5. Load persisted `TrainingHistory` when history is relevant.
6. Create an explicit `TrainingRequest` operation with an explicit `asOf`.
7. Call the application facade.
8. Branch on `TrainingResult.status`, including clarification and
   invalid/unsatisfiable outcomes.
9. Persist returned PLAN/ACTUAL/state artifacts and provenance.
10. Require host/user approval before activating a proposed adaptation.

The executable consumers under
[`examples/app-integration/`](../examples/app-integration/) exercise the same
scenario in all four languages.

## End-to-end persisted-history flow

Persist canonical PLAN and ACTUAL JSON, together with the profile and TARGET.
When the host has an explicit instant, the complete coaching flow is:

```text
persisted PLAN + ACTUAL history + profile + TARGET + explicit asOf
                              │
                              ▼
                    TrainingRequest(derive_state)
                              │
                              ▼
                       TrainingState
                              │
                              ▼
                    suggest_progression
                              │
                              ▼
                         CoachDecision[]
                              │
                              ▼
                       adapt_plan
                              │
                              ▼
                   host reviews proposed revision
```

The runnable [Swift history/state/adaptation consumer](../examples/app-integration/swift/Sources/AppIntegration/main.swift)
uses only the public SPM API and a standalone persisted input resource. The
[Kotlin](../examples/app-integration/kotlin/src/main/kotlin/AppIntegration.kt),
[Python](../examples/app-integration/python/example.py), and
[R](../examples/app-integration/r/example.R) consumers mirror the same flow.
DB++ never activates a proposal; approval and activation remain host-app
responsibilities.
