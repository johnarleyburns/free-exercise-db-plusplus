# ADR 0009: Longitudinal missing-data semantics

Status: accepted

Longitudinal output does not collapse missingness into zero. A planned session
with no ACTUAL record is `missed_planned_session`; a recorded zero-set session
is still recorded as zero. Unlinked sessions are `unplanned_session` or
`unable_to_match`. Unknown/custom exercises remain recorded and count toward
recorded-work completeness, but have no DB++ muscle totals and are reported as
`unmapped`. Other analysis states are `not_prescribed`, `not_recorded`,
`unknown`, `volume_ineligible`, and `not_applicable` where applicable.
