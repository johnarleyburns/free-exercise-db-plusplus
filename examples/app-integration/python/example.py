"""Application-contract consumer: generate, derive state, and adapt."""
import json
from pathlib import Path

from fedbpp import Database, RelationshipRegistry, TrainingRequest, process_training_request

ROOT = Path(__file__).resolve().parents[3]
db = Database.load(ROOT / "free-exercise-db-plusplus.json")
relationships = RelationshipRegistry.load(ROOT / "exercise-relationships.json")
intent = {
    "schemaVersion": "0.1.0", "intentId": "demo-intent", "subjectId": "user-123",
    "goal": "hypertrophy", "environment": "commercial_gym",
    "schedule": {"cycleLengthDays": 7, "sessionsPerCycle": {"target": 5},
                  "preferredWeekdays": ["monday", "tuesday", "wednesday", "thursday", "saturday"]},
    "sessionConstraints": {"exercisesPerSession": {"min": 3, "max": 4}},
    "useHistory": True, "historyWindow": "last_28_days",
}
request = TrainingRequest(operation="generate_from_intent", request_id="demo-generate", intent=intent,
                          as_of="2026-08-28T12:00:00Z")
result = process_training_request(request, db, relationships)
print(result.status)
if result.status in {"generated", "generated_with_target_gaps"}:
    print(json.dumps(result.plan, indent=2))

# Adaptation is a separate, explicit operation. A real app loads these values
# from persistence; this example shows the request boundary.
history = {"subjectId": "user-123", "plans": [], "workouts": [], "targets": [], "planActivations": []}
if result.plan is not None:
    adaptation = process_training_request({
        "schemaVersion": "0.1.0", "requestId": "demo-adapt", "operation": "adapt_plan",
        "profile": result.resolution["resolvedProfile"],
        "target": result.resolution["resolvedTarget"], "currentPlan": result.plan,
        "history": history, "asOf": "2026-08-28T12:00:00Z",
    }, db, relationships)
    print(adaptation.status)
