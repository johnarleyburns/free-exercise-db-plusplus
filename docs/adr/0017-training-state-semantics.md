# ADR 0017: Derived TrainingState semantics

Status: accepted (v1.7)

`TrainingState` is a deterministic, read-only summary derived from
`TrainingHistory` as of an explicit timestamp and within an explicit inclusive
history window. Timestamps honor offsets; naive timestamps require the supplied
timezone. The state does not replace PLAN or ACTUAL and is not an observational
source of truth. Active PLAN resolution uses the existing activation semantics;
the newest revision is never silently selected. Missing, unmapped, ineligible,
and unmatched observations retain their existing longitudinal states. Latest
performance and recent series are reported separately; no opaque trend is
inferred. Provenance records versions, credits, window, timezone, and inputs.
