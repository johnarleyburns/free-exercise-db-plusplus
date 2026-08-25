# PLAN-vs-ACTUAL adherence

`analyze_plan_actual(plan, workout, db)` compares one PLAN revision with one linked
ACTUAL session. Matching is explicit-reference-first and never silently fuzzy-matches
exercise names. The ACTUAL session should carry `planReference`; exercises may carry
`exercisePrescriptionId` or explicit `substitution.plannedPrescriptionId`.

Statuses are deterministic:

- `matched` — explicit prescription or one unambiguous exact exercise reference;
- `substitution` — explicit substitution metadata names the planned prescription;
- `unplanned_addition` — ACTUAL work has no PLAN prescription match;
- `missing_prescription` — a planned prescription has no ACTUAL exercise;
- `unable_to_match` — the plan/revision/session reference is absent or invalid, or an
  explicit prescription points to another session.

The result includes exercise and set rows plus effective-set adherence for muscles and
movement patterns. DB++ direct, indirect, and stabilizer semantics remain `1.0`, `0.5`,
and `0.0`; stabilizer participation is retained separately. Standalone ACTUAL records
remain valid but cannot be assigned PLAN adherence without an explicit plan reference.

```python
from src.analysis import analyze_plan_actual

result = analyze_plan_actual(plan, actual, database)
```

PLAN-vs-ACTUAL matching does not modify either source document and does not implement
fuzzy matching by default.

## Coverage and set semantics

ACTUAL resistance-volume coverage is separated into `matched`, `substitution`, `unplanned`, and `total` views. Known unplanned work contributes to total work but never satisfies an unrelated prescription; unknown/custom work remains visible in ACTUAL completeness diagnostics. Muscle adherence reports direct, indirect, stabilizer participation, and effective metrics independently.

For explicit PLAN 0.2 sets, `setPrescriptionId` wins. An invalid explicit ID is never positionally rematched, each planned set can be consumed only once, and positional fallback is used only for an unreferenced unambiguous correspondence. Set rows retain incomplete, extra, missing, substituted, and unable-to-match observations. Ranged prescriptions report minimum/target/maximum adherence rather than one percentage.
