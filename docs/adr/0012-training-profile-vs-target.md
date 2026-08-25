# ADR 0012: TrainingProfile versus TARGET

Status: accepted (v1.6)

`TrainingProfile` describes the subject and environment: equipment available,
session/time availability, experience, high-level goal context, preferences,
and exclusions. `TARGET` describes what training should accomplish, such as
effective-set ranges, exposure frequency, movement-pattern minimums, and
family coverage targets.

Hard constraints and soft preferences belong in TrainingProfile. Training
coverage goals belong in TARGET. The artifacts must not duplicate the same
concept. No PII is required. Medical diagnoses and medical record numbers do
not belong in TrainingProfile; applications may translate medical or user
context into exercise/family exclusions externally.

Goal and experience values are descriptive inputs only in v1.6. They do not
silently alter evaluation behavior.
