# ADR 0020: External progression policy assignment

Status: accepted (v1.7)

Policy assignment remains an API argument or external policy map in v1.7.
Workout PLAN schemas and TrainingProfile are unchanged. This avoids premature
portable schema churn; applications can assign different policies per
prescription and present decisions for human choice.
