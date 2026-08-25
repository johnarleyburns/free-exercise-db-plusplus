# Analysis semantics

This is the concise normative reference for the v1.1.0 PLAN / ACTUAL / TARGET analysis contract. Detailed interchange structures remain in the linked PLAN, ACTUAL, TARGET, and comparison documents.

## Artifacts and policy

PLAN describes intended prescriptions, ACTUAL records performed observations, and TARGET describes desired volume criteria. Analysis is read-only and never mutates any source document. Every result names dbpp-default-volume-v1 and records database, schema, policy, unit, period, and set-credit provenance.

The analyzed database metadata.setCredits is authoritative. The shipped values are direct 1.0, indirect 0.5, and stabilizer 0.0; these are analytical accounting credits, not physiological equivalence and not a universal stimulus score.

## Counting and coverage

Working, backoff, AMRAP, drop, cluster, rest-pause, and assisted parent sets count once. Warmup, technique, test, isometric, and other excluded set types do not count in resistance-volume totals. volumeEligible=false exercises remain visible in completeness diagnostics but contribute no muscle, effective-set, stabilizer, or movement-pattern volume.

Direct, indirect, stabilizer participation, effective sets, and movement-pattern exposure are reported separately. Unmapped/custom exercises remain visible and are reported as unmapped rather than receiving inferred roles.

## Periods, ranges, and phases

Native cycle totals are retained. A clearly labelled seven-day normalization is derived for arbitrary cycle lengths and does not alter the prescription. PLAN ranges preserve each independently supplied min, target, and max; absent bounds remain null. When a scalar is required, the representative value is target, then minimum, then maximum. Phase-specific cycles are normalized independently and cross-phase values are weighted by durationCycles.

## Matching and adherence

PLAN-vs-ACTUAL matching is explicit-reference-first and does not fuzzy-match names. Explicit substitutions identify the planned prescription while preserving the performed exercise. setPrescriptionId wins for explicit planned sets; invalid IDs are not positionally rematched, and each planned set is consumed once. Unplanned ACTUAL work contributes to total ACTUAL coverage but never satisfies an unrelated prescription.

Adherence keeps prescription completion separate from muscle-volume coverage. It reports strict prescription, substitution-adjusted completion, direct/indirect/stabilizer/effective adherence, comparable load adherence, RPE adherence, RIR adherence, and volume-load adherence only where units and quantities are meaningful. RPE and RIR are never inferred from one another, and adherence never weights effective-set credits by effort.

## Scope

The analysis describes deterministic DB++ accounting and document adherence. It does not claim physiological equivalence between exercises or substitutions, individual muscle activation, injury risk, optimal programming, or a universal stimulus/fatigue score. External interop exporters and new taxonomy/anatomy metrics are outside this release.
