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

Current parity report: Python and Swift execute the canonical non-history
resolution matrix; Kotlin and R execute every non-history fixture and their
installed/isolated consumers exercise the flagship. DB-aware unknown exercise,
equipment, and family validation is shared by all native bindings. Full
history-aware TrainingState derivation and native intent-to-plan parity remain
v1.12 work and are not claimed here.
