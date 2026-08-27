import Foundation

private func cObject(_ value: JSONValue?) -> [String: JSONValue] { value?.objectValue ?? [:] }
private func cArray(_ value: JSONValue?) -> [JSONValue] { if case .array(let values)? = value { return values }; return [] }
private func cString(_ value: JSONValue?) -> String? { if case .string(let value)? = value { return value }; return nil }

/// The released coaching policy document. Algorithms remain native code; the
/// document is kept stable so consumers can identify the policy used.
public func coachingPolicy(_ id: String = "general-adaptive-v1") -> JSONValue? {
  guard id == "general-adaptive-v1" else { return nil }
  return .object([
    "policyId": .string(id), "policyVersion": .string("1.0.0"),
    "description": .string("Conservative deterministic advisory adaptation. Ambiguous evidence holds the PLAN."),
    "stateWindowPolicy": .string("last_28_days"), "exerciseProgressionPolicy": .string("double-progression-v1"),
    "adherencePolicy": .string("quantitative-adherence-v1"), "volumeAdjustmentPolicy": .string("effective-set-one-step-v1"),
    "frequencyAdjustmentPolicy": .string("canonical-exposure-v1"), "substitutionPolicy": .string("explicit-substitution-v1"),
    "regenerationPolicy": .string("v1.8-generator-v1"),
    "decisionPriority": .array(["hard_constraints", "structural_invalidity", "target_minimums", "adherence", "repeated_failure", "progression", "target_optimization", "preferences", "continuity", "stable_tie_break"].map(JSONValue.string)),
    "parameters": .object(["minimumRecentPerformances": .number(2), "repeatedFailureThreshold": .number(2), "repeatedSkipThreshold": .number(2), "repeatedSubstitutionThreshold": .number(2), "maxSetsAddedPerMusclePerRevision": .number(1), "maxSetsRemovedPerMusclePerRevision": .number(1), "maxTotalSetChangesPerRevision": .number(2), "loadIncrement": .object(["value": .number(2.5), "unit": .string("kg")])])
  ])
}

/// Produce an advisory adaptive result. This is intentionally a pure
/// orchestration boundary: callers decide whether and when to activate the
/// proposed revision.
public func adaptPlan(profile: JSONValue, target: JSONValue, currentPlan: JSONValue,
                      history: JSONValue? = nil, asOf: String? = nil,
                      trainingState: JSONValue? = nil, database: FEDatabase,
                      policy policyId: String = "general-adaptive-v1",
                      planningPolicy: String? = nil,
                      relationships: ExerciseRelationships? = nil) -> JSONValue {
  guard let policy = coachingPolicy(policyId) else { return .object(["status": .string("invalid_input"), "currentPlan": currentPlan, "proposedPlan": .null, "decisions": .array([]), "changes": .array([]), "unresolvedIssues": .array([.object(["code": .string("UNKNOWN_COACHING_POLICY")])])]) }
  let currentEvaluation = evaluatePlan(currentPlan, database: database, profile: profile, target: target, relationships: relationships)
  let state: JSONValue
  if let trainingState { state = trainingState }
  else if let history, let asOf { state = deriveTrainingState(history, asOf: asOf, relationships: relationships, database: database) }
  else { return .object(["status": .string("insufficient_data"), "currentPlan": currentPlan, "proposedPlan": .null, "currentEvaluation": currentEvaluation, "proposedEvaluation": .null, "trainingState": .null, "decisions": .array([]), "changes": .array([]), "unresolvedIssues": .array([.object(["code": .string("INSUFFICIENT_HISTORY")])]), "policy": policy, "provenance": .object(["coachingVersion": .string("1.9.0"), "coachingPolicyId": .string(policyId)])]) }
  var proposed = currentPlan
  var decisions: [JSONValue] = [], changes: [JSONValue] = []
  let exerciseState = cObject(cObject(state)["exerciseState"])
  var sessions = cArray(cObject(proposed)["sessions"])
  for sessionIndex in sessions.indices {
    var session = cObject(sessions[sessionIndex]), exercises = cArray(session["exercises"])
    for exerciseIndex in exercises.indices {
      let rx = exercises[exerciseIndex], rxObject = cObject(rx), id = cString(rxObject["exerciseId"])
      guard let id, let stateRow = exerciseState[id] else { continue }
      let decision = applyProgressionPolicy("double-progression-v1", prescription: rx, exerciseState: stateRow, parameters: cObject(policy)["parameters"])
      let decisionObject = cObject(decision)
      decisions.append(decision)
      guard decisionObject["decisionType"] == JSONValue.string("increase_load"), let after = decisionObject["after"]?.objectValue else { continue }
      var updated = rxObject; updated["load"] = after["load"] ?? .null; exercises[exerciseIndex] = .object(updated)
      changes.append(.object(["type": .string("LOAD_INCREASED"), "prescriptionId": rxObject["prescriptionId"] ?? .null, "before": .object(["load": rxObject["load"] ?? .null]), "after": .object(["load": after["load"] ?? .null]), "reasonCodes": decisionObject["reasonCodes"] ?? .array([]), "decisionIds": .array([])]))
    }
    session["exercises"] = .array(exercises); sessions[sessionIndex] = .object(session)
  }
  var proposedObject = cObject(proposed); proposedObject["sessions"] = .array(sessions)
  if !changes.isEmpty { proposedObject["revisionId"] = .string((cString(cObject(currentPlan)["revisionId"]) ?? "r1") + "-adaptive-1") }
  proposed = .object(proposedObject)
  let proposedEvaluation = changes.isEmpty ? nil : evaluatePlan(proposed, database: database, profile: profile, target: target, relationships: relationships)
  let hardRejected = proposedEvaluation.map { cObject(cObject($0)["summary"])["satisfiesHardConstraints"] != .bool(true) } ?? false
  let accepted = !changes.isEmpty && !hardRejected
  return .object(["status": .string(accepted ? "revision_proposed" : (decisions.isEmpty ? "insufficient_data" : "no_change")), "currentPlan": currentPlan, "proposedPlan": accepted ? proposed : .null, "currentEvaluation": currentEvaluation, "proposedEvaluation": proposedEvaluation ?? .null, "trainingState": state, "decisions": .array(decisions), "changes": .array(changes), "unresolvedIssues": .array([]), "policy": policy, "provenance": .object(["coachingVersion": .string("1.9.0"), "coachingPolicyId": .string(policyId), "planningPolicyId": planningPolicy.map(JSONValue.string) ?? .null])])
}
