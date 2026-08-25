# ADR 0006: Namespaced workout extensions

Status: accepted

Extensions use namespaced objects and must not override core semantics.
Consumers may ignore unknown extensions, while migrations preserve them when
possible.
