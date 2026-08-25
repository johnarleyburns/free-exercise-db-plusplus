# ADR 0010: v1.4 history input artifact

Status: accepted

v1.4 uses the Python `TrainingHistory` API as the analysis input model and does
not introduce a versioned `training-history.schema.json`. PLAN, ACTUAL, and
TARGET remain independently versioned artifacts. The CLI accepts a small
manifest with `subjectId`, explicit `plans`, `workouts`, `targets`, and optional
`planActivations` file paths; it does not use portable glob or absolute-path
semantics. A future embedded research bundle may be proposed separately after
interchange requirements are demonstrated.
