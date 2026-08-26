# Planning policies

## `full-body-general-v1`

This is the sole v1.8 reference policy. It attempts the profile target session
count first, then lower counts before higher counts at equal distance, bounded
by the profile min/max. In the absence of a profile target its default is three
sessions. Sessions are full-body containers; target work is distributed to the
least populated session, and frequency deficits favour a session without that
muscle exposure.

Day offsets honour preferred offsets first. Remaining offsets are selected by
maximum minimum circular spacing, resolving ties by lower offset. This works
for arbitrary cycle lengths and never assumes seven days.

Each allocation is one working-set block with `6–8–10` reps and RIR 2. The
policy uses no complex planned-set structure. Candidate ranking is a published
tuple: required/locked presence, current-plan continuity, successful history
continuity, preferred exercise, preferred family, contribution to the active
deficit, avoided penalty, exerciseId. Same-family diversity is a policy
parameter for future selection refinements, not an equivalence rule.

## `upper-lower-general-v1`

This reference policy constructs alternating Upper and Lower sessions, with a
minimum of two sessions and a default of four. It uses explicit policy-owned
lists of canonical DB++ muscle IDs and movement patterns to decide whether a
candidate is compatible with an Upper or Lower session; it does not derive the
split from exercise names. Sessions are named `Upper 1`, `Lower 1`, and so on.

All filtering, allocation, coverage accounting, rep/RIR defaults, ranking,
day spacing, and evaluator acceptance behavior are the same as
`full-body-general-v1`. A required exercise is placed in a compatible split
session. A locked exercise that cannot remain at its current day offset *and*
compatible split role is explicitly unsatisfiable.

Both policies are deterministic reference constructors, not claims of optimal
physiology or coaching systems.
