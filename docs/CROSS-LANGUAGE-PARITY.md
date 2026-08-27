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

Current parity report: Python, Swift, Kotlin/JVM, and R execute every canonical
non-history resolution fixture and compare normalized result fields. DB-aware
unknown exercise, equipment, and family validation is shared by all native
bindings. Native history projections and deterministic intent-to-plan drafts
are available in all bindings; Python remains the oracle for full
adherence-rich state and production plan optimization.
