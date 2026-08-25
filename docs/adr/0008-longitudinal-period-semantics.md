# ADR 0008: Longitudinal period semantics

Status: accepted

`calendar_week` is Monday through Sunday in the analyzer timezone. `rolling_7_days`
creates a seven-day window for each date in the requested range. `plan_cycle`
uses the PLAN's native `cycle.lengthDays` and retains the native window. `phase`
expands phase cycle lengths and duration cycles. `custom_date_range` is exactly
the requested inclusive range.

Explicit timestamp offsets are honored. Naive timestamps require an analyzer
timezone; an override intentionally converts all timestamps before grouping.
The result records period type, dates, timezone, revision, and phase.

Rolling windows are emitted only when the complete seven-day window is inside
the requested range. Calendar weeks retain full Monday–Sunday bounds while
work is clipped to the requested query range. Phase expansion is finite and
does not repeat after declared phases end.
