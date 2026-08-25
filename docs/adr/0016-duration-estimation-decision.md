# ADR 0016: Duration estimation

Status: deferred (v1.6)

The current PLAN contract does not require rest intervals, set duration, or
transition timing. v1.6 therefore does not fabricate session minutes. When a
profile supplies minute limits, PlanEvaluation reports that duration is not
assessed under `duration-estimation-v1`; a future version may add a transparent
policy after the required inputs are portable and testable.
