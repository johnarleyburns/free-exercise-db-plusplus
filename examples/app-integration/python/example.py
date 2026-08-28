"""External consumer: persisted history, state, progression, and adaptation."""
import json
from pathlib import Path

from fedbpp import Database, RelationshipRegistry, TrainingRequest, process_training_request

ROOT = Path(__file__).resolve().parents[3]
db = Database.load(ROOT / "free-exercise-db-plusplus.json")
relationships = RelationshipRegistry.load(ROOT / "exercise-relationships.json")
source = TrainingRequest.load(ROOT / "fixtures/application-integration/adapt-proposal/request.json")
history = source.history
plan = source.current_plan
profile = source.profile
target = source.target
as_of = source.as_of
assert history and plan and profile and target and as_of

state_request = TrainingRequest(
    request_id="example-derive-state", operation="derive_state",
    history=history, target=target, as_of=as_of, history_window="last_28_days",
)
state_result = process_training_request(state_request, db, relationships)
assert state_result.status == "state_derived", state_result
state = state_result.training_state
print(f"state: {state['subjectId']} at {state['asOf']}")

progression_result = process_training_request(
    TrainingRequest(request_id="example-suggest-progression", operation="suggest_progression",
                    plan=plan, training_state=state), db, relationships)
if progression_result.status == "progression_available":
    print("progression decisions:", json.dumps(progression_result.coach_decisions, indent=2))
elif progression_result.status == "insufficient_data":
    print("progression: insufficient_data")
else:
    raise RuntimeError(f"progression request failed: {progression_result}")

adaptation_result = process_training_request(
    TrainingRequest(request_id="example-adapt-plan", operation="adapt_plan",
                    profile=profile, target=target, history=history,
                    current_plan=plan, as_of=as_of, options=source.options),
    db, relationships,
)
if adaptation_result.status == "no_change":
    print("adaptation: no_change")
elif adaptation_result.status in {"revision_proposed", "regeneration_proposed"}:
    proposal = adaptation_result.get("adaptation") or {}
    assert proposal.get("proposedPlan") is not None
    print("adaptation:", adaptation_result.status)
    print("coach decisions:", json.dumps(proposal.get("decisions", []), indent=2))
    print("proposed PLAN:", json.dumps(proposal["proposedPlan"], indent=2))
elif adaptation_result.status == "insufficient_data":
    print("adaptation: insufficient_data")
else:
    raise RuntimeError(f"adaptation failed: {adaptation_result}")
print("DB++ proposes only; the host app reviews, persists, approves, and activates revisions.")
