# WorkoutIntent

`WorkoutIntent` 0.1.0 is a portable, structured current planning request. It is deliberately not natural language, does not require PII, and has no model, remote-service, prompt, or conversational dependency. A consuming application may translate a conversation into this artifact.

For seven-day cycles weekdays are normative Monday-based offsets: Monday 0 through Sunday 6. Weekday fields with any other cycle length are invalid; resolver code never guesses a mapping. Session and exercise-count ranges preserve partial `min`, `target`, and `max` values. Exercise-count minimum/maximum are hard; target is a soft preference.

`resolve_intent()` returns a machine-readable `IntentResolutionResult` rather
than treating ordinary missing information as an exception. Its statuses are
`resolved`, `resolved_with_defaults`, `needs_clarification`, `invalid`, and
`unsatisfiable`; it includes resolved profile/target/policies, defaults,
warnings, conflicts, clarification descriptors, and reproducibility
provenance. `goal` and a complete schedule are required for goal/schedule
resolution. Environment/equipment is required unless an existing profile
already supplies explicit equipment. `custom` requires explicit additions.

```python
from fedbpp.intent import resolve_intent, generate_plan_from_intent

resolution = resolve_intent(intent, db, profile=None, target=None,
                            relationships=None, history=None)
result = generate_plan_from_intent(intent, db)
```

The convenience generator is strictly:

```text
resolve_intent -> optional derive_training_state -> generate_plan -> evaluate_plan
```

It returns resolution and generation output together; none of their policy
provenance is hidden. `useHistory: true` derives the existing canonical
TrainingState only when history and an explicit `as_of` value are supplied.
Missing history is warned about and is never invented. `preserve`, `neutral`,
and `vary` are deterministic selection preferences, never random rotation.

The core package does not parse natural language and has no Foundation Models,
OpenAI, Anthropic, LLM, prompt, chat, or remote-service dependency. If an app
uses a conversational model, translating its result into WorkoutIntent is the
app's responsibility.
