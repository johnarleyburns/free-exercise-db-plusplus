# ADR 0018: Explicit versioned progression policies

Status: accepted (v1.7)

Progression policies are named, versioned pure decision functions. They consume
observable state and a prescription, return an advisory decision, and never
mutate PLAN. Identical inputs and parameters produce identical output. Policy
changes require a new identifier/version; there is no hidden clock, randomness,
remote call, or AI behavior. Missing information is an explicit
`insufficient_data` decision or a documented hold.
