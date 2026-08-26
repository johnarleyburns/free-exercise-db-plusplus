# Cross-language WorkoutIntent parity

The Python v1.10.1 implementation remains the semantic oracle. The canonical
inputs are the JSON documents under `fixtures/cross-language/intent/`; object
key order and whitespace are irrelevant, while null-versus-omitted fields,
arrays, policy identities, conflicts, provenance, defaults, and override
objects are semantic.

v1.11 provides native decode/validation/result/resolution entry points in
Swift, Kotlin/JVM, and R. The native bindings share the frozen schema version
(`0.1.0`), policy IDs/versions, Monday-based weekday mapping, deterministic
equipment ordering, structured conflict codes, and stable `explicitOverrides`.

Current parity report: Python resolution is full; Swift executes the canonical
non-history resolution matrix, and Kotlin/R pass flagship and core
status-policy consumer cases. Full history-aware TrainingState and native
intent-to-plan parity remain v1.12 work and are not claimed here.
