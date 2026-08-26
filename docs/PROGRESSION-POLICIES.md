# Progression policies

Policies are deterministic, versioned advisory functions. `hold-v1` always
returns `hold` with `POLICY_HOLD`. `double-progression-v1` uses the target set
count (or explicit counted `plannedSets`), requires every required completed
working set to reach the top of its rep range, and requires every explicitly
prescribed effort value to be present and within its own RPE or RIR bounds. It
then increases a comparable mass load by the caller’s positive absolute
`loadIncrement`. Otherwise it holds, or returns `insufficient_data` when the
required observation/configuration is absent. RPE and RIR are never inferred
from one another. Machine settings, bands, bodyweight, and unknown units are
not mass-comparable. This is a reference rule, not a claim of universal
training optimality.
