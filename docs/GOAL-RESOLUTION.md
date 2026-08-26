# Goal resolution policies

Goal policies are explicit, versioned defaults rather than hidden resolver
constants. Each declares its policy ID/version, description, TARGET defaults,
PlanningPolicy, rep assumptions, effort assumptions, and methodology boundary.

`general-hypertrophy-v1` resolves hypertrophy to `full-body-general-v1`,
6--8--12 repetitions, RIR 2, and conservative target effective-set coverage:
chest 6, lats 6, quadriceps 6, and hamstrings 4 per native cycle.

`general-strength-v1` resolves strength to `full-body-general-v1`, 3--5--6
repetitions, RIR 2, and minimal generic coverage: chest 3, quadriceps 3, and
hamstrings 2. It is intentionally not an exercise-specific strength program.

These are convenience defaults, not claims of optimal programming. Explicit
TARGET fields merge over policy defaults field-by-field. An unknown requested
goal or planning policy is invalid; it is never silently substituted.
