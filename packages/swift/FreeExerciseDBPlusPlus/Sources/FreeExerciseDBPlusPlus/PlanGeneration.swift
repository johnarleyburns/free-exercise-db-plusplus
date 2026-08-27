import Foundation

private let generationPolicies: [String: [String: JSONValue]] = [
  "full-body-general-v1": [
    "policyId": .string("full-body-general-v1"), "policyVersion": .string("1"),
    "description": .string("Reference deterministic full-body construction policy."),
    "splitStrategy": .string("full_body_every_session"), "exerciseSelectionStrategy": .string("eligible_target_coverage_v1"),
    "volumeAllocationStrategy": .string("greatest_deficit_one_set_v1"), "frequencyStrategy": .string("least_exposed_session_v1"),
    "tieBreakingStrategy": .string("explicit_tuple_then_exercise_id_v1"),
    "parameters": .object(["defaultSessionsPerCycle": .number(3), "setBlock": .number(1), "reps": .object(["min": .number(6), "target": .number(8), "max": .number(10)]), "effort": .object(["rir": .number(2)]), "allowUnverifiableEquipment": .bool(false), "preferHistoryContinuity": .bool(true), "avoidSameFamilyInSession": .bool(true)])
  ],
  "upper-lower-general-v1": [
    "policyId": .string("upper-lower-general-v1"), "policyVersion": .string("1"),
    "description": .string("Reference deterministic alternating upper/lower construction policy."),
    "splitStrategy": .string("upper_lower_alternating"), "exerciseSelectionStrategy": .string("eligible_target_coverage_v1"),
    "volumeAllocationStrategy": .string("greatest_deficit_one_set_v1"), "frequencyStrategy": .string("least_exposed_compatible_session_v1"),
    "tieBreakingStrategy": .string("explicit_tuple_then_exercise_id_v1"),
    "parameters": .object(["defaultSessionsPerCycle": .number(4), "minimumSessionsPerCycle": .number(2), "setBlock": .number(1), "reps": .object(["min": .number(6), "target": .number(8), "max": .number(10)]), "effort": .object(["rir": .number(2)]), "allowUnverifiableEquipment": .bool(false), "preferHistoryContinuity": .bool(true), "avoidSameFamilyInSession": .bool(true)])
  ]
]

private func gObject(_ value: JSONValue?) -> [String: JSONValue] { value?.objectValue ?? [:] }
private func gString(_ value: JSONValue?) -> String? { if case .string(let value)? = value { return value }; return nil }
private func gNumber(_ value: JSONValue?) -> Double? { if case .number(let value)? = value { return value }; return nil }
private func gArray(_ value: JSONValue?) -> [JSONValue] { if case .array(let value)? = value { return value }; return [] }
private func gIntArray(_ value: JSONValue?) -> [Int] { gArray(value).compactMap { gNumber($0).map(Int.init) ?? gString($0).flatMap(Int.init) } }
private func gRange(_ value: JSONValue?) -> (min: Double?, target: Double?, max: Double?) { let o = gObject(value); return (gNumber(o["min"]), gNumber(o["target"]), gNumber(o["max"])) }
private func gStringArray(_ value: JSONValue?) -> [String] { gArray(value).compactMap(gString) }
private func gPolicy(_ id: String) -> JSONValue { .object(generationPolicies[id] ?? [:]) }

private func generationOffsets(cycle: Int, count: Int, preferred: [Int], excluded: Set<Int>) -> [Int]? {
  let allowed = (0..<cycle).filter { !excluded.contains($0) }
  guard allowed.count >= count else { return nil }
  var chosen = preferred.filter { allowed.contains($0) }
  while chosen.count < count {
    let choices = allowed.filter { !chosen.contains($0) }
    let next = choices.min { a, b in
      func spacing(_ value: Int) -> Int { chosen.isEmpty ? cycle : chosen.map { min((value - $0 + cycle) % cycle, ($0 - value + cycle) % cycle) }.min()! }
      let sa = spacing(a), sb = spacing(b)
      return sa == sb ? a < b : sa > sb
    }!
    chosen.append(next)
  }
  return chosen.sorted()
}

/// Native deterministic production generator. It returns the same top-level
/// result concepts as Python: status, plan, evaluation, policy, rationale,
/// unsatisfied findings, and provenance.
public func generatePlan(profile: JSONValue, target: JSONValue, database: FEDatabase,
                         policy policyId: String = "full-body-general-v1",
                         relationships: ExerciseRelationships? = nil,
                         trainingState: JSONValue? = nil,
                         currentPlan: JSONValue? = nil,
                         requiredExerciseIds: [String] = [], lockedExerciseIds: [String] = [],
                         additionalExclusions: [String] = [], options: JSONValue? = nil) -> JSONValue {
  let profileObject = gObject(profile), targetObject = gObject(target)
  guard let policy = generationPolicies[policyId] else { return .object(["status": .string("invalid_input"), "plan": .null, "evaluation": .null, "policy": .object([:]), "selectionRationale": .array([]), "unsatisfiedConstraints": .array([.object(["code": .string("UNKNOWN_PLANNING_POLICY")])]), "unsatisfiedTargets": .array([]), "unsatisfiedSoftPreferences": .array([]), "provenance": .object(["generatorVersion": .string("0.1.0")])]) }
  let provenance: [String: JSONValue] = [
    "generatorVersion": .string("0.1.0"), "policyId": .string(policyId), "policyVersion": policy["policyVersion"] ?? .string("1"),
    "dbSchemaVersion": database.metadata["schemaVersion"] ?? .null, "dbConverterVersion": database.metadata["converterVersion"] ?? .null,
    "dbUpstreamSha256": database.metadata["upstream"]?.objectValue?["sha256"] ?? .null,
    "trainingProfileSchemaVersion": profileObject["schemaVersion"] ?? .null, "targetSchemaVersion": targetObject["schemaVersion"] ?? .null,
    "trainingStateVersion": gObject(trainingState)["stateVersion"] ?? .null,
    "relationshipSchemaVersion": relationships.map { .string($0.schemaVersion) } ?? .null,
    "analysisPolicy": .string("dbpp-default-volume-v1"), "setCredits": .object(["direct": .number(database.setCredits.direct), "indirect": .number(database.setCredits.indirect), "stabilizer": .number(database.setCredits.stabilizer)])
  ]
  func result(_ status: String, _ plan: JSONValue?, _ evaluation: JSONValue?, constraints: [JSONValue] = [], targets: [JSONValue] = [], soft: [JSONValue] = [], rationale: [JSONValue] = []) -> JSONValue {
    .object(["status": .string(status), "plan": plan ?? .null, "evaluation": evaluation ?? .null, "policy": .object(policy), "selectionRationale": .array(rationale), "unsatisfiedConstraints": .array(constraints), "unsatisfiedTargets": .array(targets), "unsatisfiedSoftPreferences": .array(soft), "provenance": .object(provenance)])
  }
  guard !profileObject.isEmpty && !targetObject.isEmpty else { return result("invalid_input", nil, nil, constraints: [.object(["code": .string("INVALID_INPUT")])]) }
  let availability = gObject(profileObject["availability"]), sessionRange = gRange(availability["sessionsPerCycle"])
  let defaultCount = Int(gNumber(gObject(policy["parameters"])["defaultSessionsPerCycle"]) ?? 3)
  let sessionCount = Int(sessionRange.target ?? sessionRange.min ?? Double(defaultCount))
  let cycle = Int(gNumber(availability["cycleLengthDays"]) ?? gNumber(targetObject["periodDays"]) ?? 7)
  let excludedDays = Set(gIntArray(availability["excludedDayOffsets"]))
  let preferredDays = gIntArray(availability["preferredDayOffsets"])
  guard let offsets = generationOffsets(cycle: cycle, count: max(1, sessionCount), preferred: preferredDays, excluded: excludedDays) else { return result("unsatisfiable", nil, nil, constraints: [.object(["code": .string("SESSION_COUNT_CONFLICT")])]) }
  let constraints = gObject(profileObject["constraints"]), excluded = Set(gStringArray(constraints["excludedExerciseIds"]) + additionalExclusions), required = Set(requiredExerciseIds + lockedExerciseIds)
  let availableEquipment = Set(gStringArray(profileObject["equipment"]))
  let candidates = database.allExercises.values.filter { exercise in
    guard exercise.annotation.volumeEligible, !excluded.contains(exercise.exerciseId) else { return false }
    guard let equipment = gString(exercise.source?["equipment"]) else { return false }
    return availableEquipment.contains(equipment)
  }.sorted { $0.exerciseId < $1.exerciseId }
  let candidateById = Dictionary(uniqueKeysWithValues: candidates.map { ($0.exerciseId, $0) })
  let missingRequired = required.subtracting(candidateById.keys).sorted()
  guard missingRequired.isEmpty else { return result("unsatisfiable", nil, nil, constraints: missingRequired.map { .object(["code": .string("NO_ELIGIBLE_EXERCISE"), "exerciseId": .string($0)]) }) }
  let reps = gObject(policy["parameters"])["reps"] ?? .object([:]), effort = gObject(policy["parameters"])["effort"] ?? .object([:])
  let planId = gString(gObject(options)["planId"]) ?? "generated-plan", revisionId = gString(gObject(options)["revisionId"]) ?? "r1", planName = gString(gObject(options)["name"]) ?? "Generated \(policyId)"
  var sessions: [[String: JSONValue]] = offsets.enumerated().map { index, offset in ["planSessionId": .string("session-\(index + 1)"), "dayOffset": .number(Double(offset)), "name": .string("Session \(index + 1)"), "exercises": .array([])] }
  var rationale: [String: Set<String>] = [:]
  func family(_ id: String) -> String? { relationships?.family(for: id)?.familyId }
  func add(_ id: String, _ session: Int, _ reason: String) {
    var exercises = gArray(sessions[session]["exercises"])
    if let index = exercises.firstIndex(where: { gString(gObject($0)["exerciseId"]) == id }) {
      var item = gObject(exercises[index]); item["sets"] = .number((gNumber(item["sets"]) ?? 0) + 1); exercises[index] = .object(item)
    } else {
      let order = exercises.count + 1, name = gString(candidateById[id]?.source?["name"]) ?? id
      exercises.append(.object(["prescriptionId": .string(String(format: "rx-%02d-%02d", session + 1, order)), "exerciseId": .string(id), "exerciseName": .string(name), "order": .number(Double(order)), "sets": .number(1), "reps": reps, "effort": effort, "setType": .string("working")]))
    }
    sessions[session]["exercises"] = .array(exercises); rationale[id, default: []].insert(reason)
  }
  for id in required.sorted() { add(id, 0, "REQUIRED_EXERCISE") }
  let targetMuscles = gObject(targetObject["muscles"]), targetPatterns = gObject(targetObject["movementPatterns"])
  func contribution(_ exercise: Exercise, _ key: String) -> Double { exercise.annotation.direct.contains(key) ? database.setCredits.direct : (exercise.annotation.indirect.contains(key) ? database.setCredits.indirect : 0) }
  var guardCount = 0
  while guardCount < 256 {
    guardCount += 1
    var deficits: [(Double, String, String)] = []
    for (muscle, rangeValue) in targetMuscles { let range = gRange(rangeValue), actual = sessions.flatMap { gArray($0["exercises"]) }.reduce(0.0) { total, raw in total + (candidateById[gString(gObject(raw)["exerciseId"]) ?? ""].map { contribution($0, muscle) * (gNumber(gObject(raw)["sets"]) ?? 0) } ?? 0) }; if let minimum = range.min, actual < minimum { deficits.append((minimum - actual, "muscle", muscle)) }; if let target = range.target, actual < target { deficits.append((target - actual, "muscle", muscle)) } }
    for (pattern, value) in targetPatterns { let range = gRange(value), actual = sessions.flatMap { gArray($0["exercises"]) }.reduce(0.0) { total, raw in total + (candidateById[gString(gObject(raw)["exerciseId"]) ?? ""]?.annotation.patterns.contains(pattern) == true ? (gNumber(gObject(raw)["sets"]) ?? 0) : 0) }; if let minimum = range.min, actual < minimum { deficits.append((minimum - actual, "pattern", pattern)) } }
    guard let deficit = deficits.sorted(by: { $0.0 == $1.0 ? ($0.1, $0.2) < ($1.1, $1.2) : $0.0 > $1.0 }).first else { break }
    let eligible = candidates.filter { deficit.1 == "muscle" ? contribution($0, deficit.2) > 0 : $0.annotation.patterns.contains(deficit.2) }
    guard let candidate = eligible.first else { break }
    let choices = sessions.indices.sorted { a, b in gArray(sessions[a]["exercises"]).count < gArray(sessions[b]["exercises"]).count }
    guard let session = choices.first(where: { !gArray(sessions[$0]["exercises"]).contains { family(gString($0.objectValue?["exerciseId"]) ?? "") == family(candidate.exerciseId) && family(candidate.exerciseId) != nil } }) else { break }
    add(candidate.exerciseId, session, "TARGET_COVERAGE")
  }
  let plan: JSONValue = .object(["schemaVersion": .string("0.2.0"), "planId": .string(planId), "revisionId": .string(revisionId), "name": .string(planName), "description": .null, "cycle": .object(["lengthDays": .number(Double(cycle))]), "sessions": .array(sessions.map(JSONValue.object))])
  let evaluation = evaluatePlan(plan, database: database, profile: profile, target: target, relationships: relationships)
  let typedPlanValid = (try? JSONDecoder().decode(WorkoutPlan.self, from: JSONEncoder().encode(plan))) != nil
  guard typedPlanValid else { return result("unsatisfiable", nil, evaluation, constraints: [.object(["code": .string("INVALID_GENERATED_PLAN")])], rationale: rationale.sorted { $0.key < $1.key }.map { .object(["exerciseId": .string($0.key), "reasonCodes": .array($0.value.sorted().map(JSONValue.string))]) }) }
  let hard = gObject(gObject(evaluation)["summary"])["satisfiesHardConstraints"] == .bool(true)
  let status = hard ? "generated" : "unsatisfiable"
  return result(status, plan, evaluation, rationale: rationale.sorted { $0.key < $1.key }.map { .object(["exerciseId": .string($0.key), "reasonCodes": .array($0.value.sorted().map(JSONValue.string))]) })
}
