# ADR 0007: PLAN activation and longitudinal linkage

Status: accepted

Longitudinal analysis resolves an ACTUAL session to a PLAN revision in this
order:

1. the ACTUAL `planReference.revisionId` (and `planId`, when present);
2. an explicit activation/effective window supplied by the history or plan;
3. an explicitly configured analyzer fallback revision;
4. unresolved.

The analyzer never assumes that the latest revision applies historically.
Overlapping activation windows are an error. Unresolved sessions remain in the
session table with `unable_to_match`; they are not converted into planned work.

Scheduled contributions use `effectiveFrom` inclusive and `effectiveTo`
exclusive. Explicit linkage does not bypass the scheduled-local-date check.
