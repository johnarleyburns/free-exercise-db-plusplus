import Foundation

private func cObject(_ value: JSONValue?) -> [String: JSONValue] { value?.objectValue ?? [:] }
private func cArray(_ value: JSONValue?) -> [JSONValue] { if case .array(let values)? = value { return values }; return [] }
private func cString(_ value: JSONValue?) -> String? { if case .string(let value)? = value { return value }; return nil }
private func cNumber(_ value: JSONValue?) -> Double? { if case .number(let value)? = value { return value }; return nil }

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
  func resultProvenance() -> JSONValue {
    .object([
      "coachingVersion": .string("1.9.0"), "coachingPolicyId": .string(policyId),
      "coachingPolicyVersion": .string("1.0.0"), "planningPolicyId": planningPolicy.map(JSONValue.string) ?? .null,
      "trainingStateVersion": cObject(state)["stateVersion"] ?? .null,
      "historyWindow": cObject(state)["historyWindow"] ?? .null,
      "stateProvenance": cObject(state)["provenance"] ?? .null,
      "dbSchemaVersion": database.metadata["schemaVersion"] ?? .null,
      "dbConverterVersion": database.metadata["converterVersion"] ?? .null,
      "dbUpstreamSha256": database.metadata["upstream"]?.objectValue?["sha256"] ?? .null,
      "setCredits": .object(["direct": .number(database.setCredits.direct), "indirect": .number(database.setCredits.indirect), "stabilizer": .number(database.setCredits.stabilizer)]),
      "evaluationVersion": .string("0.1.0")
    ])
  }
  let proposedRevision: String = {
    guard let current = cString(cObject(currentPlan)["revisionId"]) else { return "r2" }
    if current.hasPrefix("r"), let number = Int(current.dropFirst()) { return "r\(number + 1)" }
    return current + "-adaptive-1"
  }()
  if cObject(cObject(currentEvaluation)["summary"])["satisfiesHardConstraints"] != .bool(true) {
    let generated = generatePlan(profile: profile, target: target, database: database,
      policy: planningPolicy ?? "full-body-general-v1", relationships: relationships,
      trainingState: state, currentPlan: currentPlan,
      options: .object(["planId": cObject(currentPlan)["planId"] ?? .string("generated-plan"), "revisionId": .string(proposedRevision)]))
    if let proposed = cObject(generated)["plan"], proposed != .null {
      let decision: JSONValue = .object(["decisionId": .string("decision-regenerate"), "decisionType": .string("regenerate_plan"), "policyId": .string(policyId), "policyVersion": .string("1.0.0"), "planId": cObject(currentPlan)["planId"] ?? .null, "revisionId": cObject(currentPlan)["revisionId"] ?? .null, "prescriptionId": .null, "exerciseId": .null, "before": .object([:]), "after": .object([:]), "reasonCodes": .array([.string("PLAN_REGENERATION_REQUIRED")]), "evidence": .object(cObject(cObject(currentEvaluation)["constraints"])), "provenance": cObject(state)["provenance"] ?? .object([:])])
      let change: JSONValue = .object(["type": .string("PLAN_REGENERATED"), "reasonCodes": .array([.string("PLAN_REGENERATION_REQUIRED")]), "decisionIds": .array([.string("decision-regenerate")])])
      return .object(["status": .string("regeneration_proposed"), "currentPlan": currentPlan, "proposedPlan": proposed, "currentEvaluation": currentEvaluation, "proposedEvaluation": cObject(generated)["evaluation"] ?? .null, "trainingState": state, "decisions": .array([decision]), "changes": .array([change]), "unresolvedIssues": .array([]), "policy": policy, "provenance": resultProvenance()])
    }
  }
  var proposed = currentPlan
  var decisions: [JSONValue] = [], changes: [JSONValue] = []
  let exerciseState = cObject(cObject(state)["exerciseState"])
  let progressionPolicy = cString(cObject(policy)["exerciseProgressionPolicy"]) ?? "double-progression-v1"
  let substitutionHistory = cObject(cObject(cObject(state)["adherenceState"])["substitutionHistoryByPrescription"])
  var sessions = cArray(cObject(proposed)["sessions"])
  for sessionIndex in sessions.indices {
    var session = cObject(sessions[sessionIndex]), exercises = cArray(session["exercises"])
    for exerciseIndex in exercises.indices {
      let rx = exercises[exerciseIndex], rxObject = cObject(rx), id = cString(rxObject["exerciseId"])
      guard let id, let stateRow = exerciseState[id] else { continue }
      if let prescriptionId = cString(rxObject["prescriptionId"]) {
        let skipped = cNumber(cObject(cObject(state)["adherenceState"])["skippedPrescriptionCounts"]?.objectValue?[prescriptionId]) ?? 0
        if skipped >= 2 {
          decisions.append(.object(["schemaVersion": .string("0.1.0"), "decisionId": .string("decision-hold-\(prescriptionId)"), "decisionType": .string("hold"), "policyId": .string(policyId), "policyVersion": .string("1.0.0"), "planId": cObject(currentPlan)["planId"] ?? .null, "revisionId": cObject(currentPlan)["revisionId"] ?? .null, "prescriptionId": .string(prescriptionId), "exerciseId": .string(id), "before": .object([:]), "after": .object([:]), "reasonCodes": .array([.string("REPEATEDLY_SKIPPED")]), "evidence": .object(["skippedPrescriptionCount": .number(skipped)]), "provenance": cObject(state)["provenance"] ?? .object([:])]))
        }
        let substitution = cObject(substitutionHistory[prescriptionId])
        let count = substitution["count"].flatMap { if case .number(let value) = $0 { return value }; return nil } ?? 0
        if count >= 2, let replacement = cString(substitution["replacementExerciseId"]), let replacementExercise = try? database.getExercise(replacement), replacementExercise.annotation.volumeEligible {
        var updated = rxObject; updated["exerciseId"] = .string(replacement); exercises[exerciseIndex] = .object(updated)
        let decisionId = "substitute_exercise-\(prescriptionId)"
        decisions.append(.object(["schemaVersion": .string("0.1.0"), "decisionId": .string(decisionId), "decisionType": .string("substitute_exercise"), "policyId": .string(policyId), "policyVersion": .string("1.0.0"), "planId": cObject(currentPlan)["planId"] ?? .null, "revisionId": cObject(currentPlan)["revisionId"] ?? .null, "prescriptionId": .string(prescriptionId), "exerciseId": .string(id), "before": .object(["exerciseId": .string(id)]), "after": .object(["exerciseId": .string(replacement)]), "reasonCodes": .array([.string("REPEATED_SUBSTITUTION")]), "evidence": .object(substitution), "provenance": cObject(state)["provenance"] ?? .object([:])]))
        changes.append(.object(["type": .string("EXERCISE_SUBSTITUTED"), "prescriptionId": .string(prescriptionId), "before": .object(["exerciseId": .string(id)]), "after": .object(["exerciseId": .string(replacement)]), "reasonCodes": .array([.string("REPEATED_SUBSTITUTION")]), "decisionIds": .array([.string(decisionId)])]))
        continue
        }
      }
      var normalizedDecision = cObject(applyProgressionPolicy(progressionPolicy, prescription: rx, exerciseState: stateRow, parameters: cObject(policy)["parameters"]))
      if let prescriptionId = cString(rxObject["prescriptionId"]), let decisionType = cString(normalizedDecision["decisionType"]) {
        normalizedDecision["decisionId"] = .string("decision-\(decisionType)-\(prescriptionId)")
      }
      normalizedDecision["planId"] = cObject(currentPlan)["planId"] ?? .null
      normalizedDecision["revisionId"] = cObject(currentPlan)["revisionId"] ?? .null
      normalizedDecision["provenance"] = cObject(state)["provenance"] ?? .object([:])
      let decision = JSONValue.object(normalizedDecision)
      let decisionObject = normalizedDecision
      decisions.append(decision)
      guard decisionObject["decisionType"] == JSONValue.string("increase_load"), let after = decisionObject["after"]?.objectValue else { continue }
      var updated = rxObject; updated["load"] = after["load"] ?? .null; exercises[exerciseIndex] = .object(updated)
      changes.append(.object(["type": .string("LOAD_CHANGED"), "prescriptionId": rxObject["prescriptionId"] ?? .null, "exerciseId": rxObject["exerciseId"] ?? .null, "before": .object(rxObject), "after": .object(updated), "reasonCodes": .array([.string("PROGRESSION_CRITERIA_MET")]), "decisionIds": .array([decisionObject["decisionId"] ?? .null])]))
    }
    session["exercises"] = .array(exercises); sessions[sessionIndex] = .object(session)
  }
  var proposedObject = cObject(proposed); proposedObject["sessions"] = .array(sessions)
  if !changes.isEmpty { proposedObject["revisionId"] = .string(proposedRevision) }
  proposed = .object(proposedObject)
  let proposedEvaluation = changes.isEmpty ? nil : evaluatePlan(proposed, database: database, profile: profile, target: target, relationships: relationships)
  let hardRejected = proposedEvaluation.map { cObject(cObject($0)["summary"])["satisfiesHardConstraints"] != .bool(true) } ?? false
  func excesses(_ evaluation: JSONValue) -> [String: Double] {
    let root = cObject(evaluation), sections = [cObject(root["muscleCoverage"]), cObject(root["frequency"]), cObject(root["movementPatterns"]), cObject(cObject(root["families"])["targets"])]
    var result: [String: Double] = [:]
    for rows in sections { for (key, raw) in rows { let row = cObject(raw), actual = cNumber(row["actualEffectiveSets"]) ?? cNumber(row["normalizedExposuresPer7Days"]) ?? cNumber(row["plannedSets"]) ?? 0; if let max = cNumber(row["maximum"]), actual > max { result[key] = actual - max } } }
    return result
  }
  let currentExcess = excesses(currentEvaluation), proposedExcess = proposedEvaluation.map(excesses) ?? [:]
  let worsensMaximum = proposedExcess.contains { key, value in value > (currentExcess[key] ?? 0) }
  let gateRejected = hardRejected || worsensMaximum
  let accepted = !changes.isEmpty && !gateRejected
  func keyLess(_ left: [String], _ right: [String]) -> Bool {
    for (l, r) in zip(left, right) { if l != r { return l < r } }
    return left.count < right.count
  }
  let orderedDecisions = decisions.sorted { left, right in
    let l = cObject(left), r = cObject(right)
    return keyLess([cString(l["prescriptionId"]) ?? "", cString(l["decisionType"]) ?? "", cString(l["decisionId"]) ?? ""], [cString(r["prescriptionId"]) ?? "", cString(r["decisionType"]) ?? "", cString(r["decisionId"]) ?? ""])
  }
  let orderedChanges = changes.sorted { left, right in
    let l = cObject(left), r = cObject(right)
    return keyLess([cString(l["prescriptionId"]) ?? "", cString(l["type"]) ?? ""], [cString(r["prescriptionId"]) ?? "", cString(r["type"]) ?? ""])
  }
  return .object(["status": .string(gateRejected ? "unsatisfiable" : (accepted ? "revision_proposed" : (orderedDecisions.isEmpty ? "insufficient_data" : "no_change"))), "currentPlan": currentPlan, "proposedPlan": gateRejected ? .null : (accepted ? proposed : .null), "currentEvaluation": currentEvaluation, "proposedEvaluation": proposedEvaluation ?? .null, "trainingState": state, "decisions": .array(orderedDecisions), "changes": .array(orderedChanges), "unresolvedIssues": .array(gateRejected ? [.object(["code": .string("EVALUATOR_GATE_REJECTED")])] : []), "policy": policy, "provenance": resultProvenance()])
}
