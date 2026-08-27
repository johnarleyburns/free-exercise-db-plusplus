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
    "parameters": .object([
      "defaultSessionsPerCycle": .number(4), "minimumSessionsPerCycle": .number(2), "setBlock": .number(1),
      "reps": .object(["min": .number(6), "target": .number(8), "max": .number(10)]), "effort": .object(["rir": .number(2)]),
      "allowUnverifiableEquipment": .bool(false), "preferHistoryContinuity": .bool(true), "avoidSameFamilyInSession": .bool(true),
      "upperMuscles": .array(["chest", "lats", "middle_back", "traps", "biceps", "triceps", "shoulders", "forearms", "rotator_cuff"].map(JSONValue.string)),
      "lowerMuscles": .array(["quadriceps", "hamstrings", "glutes", "calves", "abductors", "adductors", "hip_flexors", "lower_back"].map(JSONValue.string)),
      "upperPatterns": .array(["horizontal_press", "horizontal_press_triceps_bias", "incline_press", "decline_press", "vertical_press", "horizontal_pull", "vertical_pull", "chest_fly", "elbow_extension", "elbow_flexion", "shoulder_abduction", "shoulder_flexion", "shoulder_external_rotation", "shoulder_internal_rotation", "face_pull", "reverse_fly", "shrug", "upright_row"].map(JSONValue.string)),
      "lowerPatterns": .array(["squat", "squat_quad_bias", "lunge", "step_up", "leg_press", "hip_hinge", "hip_extension", "hip_flexion", "knee_extension", "knee_flexion", "plantar_flexion_bent_knee", "plantar_flexion_straight_knee", "hip_abduction", "hip_adduction"].map(JSONValue.string))
    ])
  ]
]

private struct CandidateRank: Comparable {
  let required: Int
  let continuity: Int
  let history: Int
  let preferred: Int
  let preferredFamily: Int
  let contribution: Double
  let avoided: Int
  let exerciseId: String

  static func < (lhs: CandidateRank, rhs: CandidateRank) -> Bool {
    if lhs.required != rhs.required { return lhs.required < rhs.required }
    if lhs.continuity != rhs.continuity { return lhs.continuity < rhs.continuity }
    if lhs.history != rhs.history { return lhs.history < rhs.history }
    if lhs.preferred != rhs.preferred { return lhs.preferred < rhs.preferred }
    if lhs.preferredFamily != rhs.preferredFamily { return lhs.preferredFamily < rhs.preferredFamily }
    if lhs.contribution != rhs.contribution { return lhs.contribution < rhs.contribution }
    if lhs.avoided != rhs.avoided { return lhs.avoided < rhs.avoided }
    return lhs.exerciseId < rhs.exerciseId
  }
}

private func gObject(_ value: JSONValue?) -> [String: JSONValue] { value?.objectValue ?? [:] }
private func gString(_ value: JSONValue?) -> String? { if case .string(let value)? = value { return value }; return nil }
private func gNumber(_ value: JSONValue?) -> Double? { if case .number(let value)? = value { return value }; return nil }
private func gArray(_ value: JSONValue?) -> [JSONValue] { if case .array(let value)? = value { return value }; return [] }
private func gIntArray(_ value: JSONValue?) -> [Int] { gArray(value).compactMap { gNumber($0).map(Int.init) ?? gString($0).flatMap(Int.init) } }
private func gRange(_ value: JSONValue?) -> (min: Double?, target: Double?, max: Double?) { let o = gObject(value); return (gNumber(o["min"]), gNumber(o["target"]), gNumber(o["max"])) }
private func gStringArray(_ value: JSONValue?) -> [String] { gArray(value).compactMap(gString) }
public func planningPolicy(_ id: String) -> JSONValue? { generationPolicies[id].map(JSONValue.object) }

private func generationOffsets(cycle: Int, count: Int, preferred: [Int], excluded: Set<Int>, locked: [Int] = []) -> [Int]? {
  let allowed = (0..<cycle).filter { !excluded.contains($0) }
  guard allowed.count >= count else { return nil }
  guard locked.count <= count, locked.allSatisfy({ allowed.contains($0) }) else { return nil }
  var chosen = Array(Set(locked)).sorted()
  chosen += preferred.filter { allowed.contains($0) && !chosen.contains($0) }
  chosen = Array(chosen.prefix(count))
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
                         requiredFamilyIds: [String] = [],
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
  let currentSessions = gArray(gObject(currentPlan)["sessions"])
  var lockedLocations: [String: [Int]] = [:]
  for id in lockedExerciseIds {
    lockedLocations[id] = currentSessions.compactMap { raw in
      let session = gObject(raw), ids = gArray(session["exercises"]).compactMap { gString(gObject($0)["exerciseId"]) }
      guard ids.contains(id) else { return nil }
      return gNumber(session["dayOffset"]).map(Int.init)
    }
  }
  let lockedOffsets = Set(lockedLocations.values.flatMap { $0 })
  let lockedConflict: (String?, String?) -> JSONValue = { id, detail in
    var object: [String: JSONValue] = ["code": .string("LOCKED_EXERCISE_CONFLICT")]
    if let id { object["exerciseId"] = .string(id) }
    if let detail { object["detail"] = .string(detail) }
    return .object(object)
  }
  if let missing = lockedExerciseIds.sorted().first(where: { (lockedLocations[$0] ?? []).isEmpty }) {
    return result("unsatisfiable", nil, nil, constraints: [lockedConflict(missing, "locked exercises require currentPlan and the exercise must occur in it")])
  }
  if lockedOffsets.count > max(1, sessionCount) {
    return result("unsatisfiable", nil, nil, constraints: [lockedConflict(lockedExerciseIds.sorted().first ?? "", "too many locked current-plan offsets for requested session count")])
  }
  if lockedLocations.values.flatMap({ $0 }).count != lockedOffsets.count {
    return result("unsatisfiable", nil, nil, constraints: [lockedConflict(nil, "multiple locked current-plan sessions share a dayOffset")])
  }
  if lockedOffsets.contains(where: { $0 < 0 || $0 >= cycle || excludedDays.contains($0) }) {
    return result("unsatisfiable", nil, nil, constraints: [lockedConflict(lockedExerciseIds.sorted().first ?? "", "locked current-plan dayOffset is unavailable in generated cycle")])
  }
  guard let offsets = generationOffsets(cycle: cycle, count: max(1, sessionCount), preferred: preferredDays, excluded: excludedDays, locked: Array(lockedOffsets)) else { return result("unsatisfiable", nil, nil, constraints: [.object(["code": .string("SESSION_COUNT_CONFLICT")])]) }
  let constraints = gObject(profileObject["constraints"]), excluded = Set(gStringArray(constraints["excludedExerciseIds"]) + additionalExclusions), excludedFamilies = Set(gStringArray(constraints["excludedFamilyIds"])), required = Set(requiredExerciseIds + lockedExerciseIds), requiredFamilies = Set(requiredFamilyIds)
  var availableEquipment = Set(gStringArray(profileObject["equipment"]))
  if !availableEquipment.isDisjoint(with: ["bodyweight", "no equipment", "none"]) { availableEquipment.insert("body only") }
  let candidates = database.allExercises.values.filter { exercise in
    guard exercise.annotation.volumeEligible, !excluded.contains(exercise.exerciseId) else { return false }
    guard let equipment = gString(exercise.source?["equipment"]) else { return false }
    return availableEquipment.contains(equipment) && !excludedFamilies.contains(relationships?.family(for: exercise.exerciseId)?.familyId ?? "")
  }.sorted { $0.exerciseId < $1.exerciseId }
  let candidateById = Dictionary(uniqueKeysWithValues: candidates.map { ($0.exerciseId, $0) })
  let missingRequired = required.subtracting(candidateById.keys).sorted()
  guard missingRequired.isEmpty else {
    let findings = missingRequired.map { id -> JSONValue in
      if lockedExerciseIds.contains(id) { return lockedConflict(id, excluded.contains(id) ? "locked exercise is excluded" : "locked exercise is unavailable") }
      return .object(["code": .string("NO_ELIGIBLE_EXERCISE"), "exerciseId": .string(id)])
    }
    return result("unsatisfiable", nil, nil, constraints: findings)
  }
  let currentIds = Set(gArray(gObject(currentPlan)["sessions"]).flatMap { gArray(gObject($0)["exercises"]) }.compactMap { gString(gObject($0)["exerciseId"]) })
  let history = gObject(gObject(trainingState)["exerciseState"])
  let preferredIds = Set(gStringArray(gObject(profileObject["exercisePreferences"])["preferredExerciseIds"]))
  let avoidedIds = Set(gStringArray(gObject(profileObject["exercisePreferences"])["avoidedExerciseIds"]))
  let preferredFamilies = Set(gStringArray(gObject(profileObject["exercisePreferences"])["preferredFamilyIds"]))
  let avoidedFamilies = Set(gStringArray(gObject(profileObject["exercisePreferences"])["avoidedFamilyIds"]))
  let continuity = gString(gObject(options)["continuity"]) ?? "preserve"
  guard ["preserve", "neutral", "vary"].contains(continuity) else {
    return result("invalid_input", nil, nil, constraints: [.object(["code": .string("INVALID_INPUT"), "detail": .string("options.continuity must be preserve, neutral, or vary")])])
  }
  func family(_ id: String) -> String? { relationships?.family(for: id)?.familyId }
  func contribution(_ exercise: Exercise, _ kind: String, _ key: String) -> Double {
    if kind == "pattern" { return exercise.annotation.patterns.contains(key) ? 1 : 0 }
    if kind == "family" { return family(exercise.exerciseId) == key ? 1 : 0 }
    if kind == "frequency" {
      return (exercise.annotation.direct.contains(key) || exercise.annotation.indirect.contains(key)) ? 1 : 0
    }
    return exercise.annotation.direct.contains(key) ? database.setCredits.direct
      : (exercise.annotation.indirect.contains(key) ? database.setCredits.indirect
      : (exercise.annotation.stabilizers.contains(key) ? database.setCredits.stabilizer : 0))
  }
  func rank(_ candidate: Exercise, _ kind: String, _ key: String) -> CandidateRank {
    let state = gObject(history[candidate.exerciseId])
    let adherence = gNumber(gObject(state["prescriptionAdherence"])["setAdherence"])
    let goodHistory = history[candidate.exerciseId] != nil && (adherence == nil || adherence! >= 0.5)
    let current = currentIds.contains(candidate.exerciseId) ? 1 : 0
    let good = goodHistory ? 1 : 0
    let continuityRank: (Int, Int)
    if continuity == "preserve" { continuityRank = (-current, -good) }
    else if continuity == "neutral" { continuityRank = (0, 0) }
    else { continuityRank = (current, good) }
    let familyId = family(candidate.exerciseId)
    let preferred = preferredIds.contains(candidate.exerciseId) ? -1 : 0
    let preferredFamily = familyId.map { preferredFamilies.contains($0) ? -1 : 0 } ?? 0
    let avoided = (avoidedIds.contains(candidate.exerciseId) ? 1 : 0) + (familyId.map { avoidedFamilies.contains($0) ? 1 : 0 } ?? 0)
    return CandidateRank(required: required.contains(candidate.exerciseId) ? -1 : 0, continuity: continuityRank.0,
                         history: continuityRank.1, preferred: preferred, preferredFamily: preferredFamily,
                         contribution: -contribution(candidate, kind, key), avoided: avoided,
                         exerciseId: candidate.exerciseId)
  }
  func ranked(_ kind: String, _ key: String) -> [Exercise] {
    candidates.sorted { rank($0, kind, key) < rank($1, kind, key) }
  }
  let reps = gObject(policy["parameters"])["reps"] ?? .object([:]), effort = gObject(policy["parameters"])["effort"] ?? .object([:])
  let planId = gString(gObject(options)["planId"]) ?? "generated-plan", revisionId = gString(gObject(options)["revisionId"]) ?? "r1", planName = gString(gObject(options)["name"]) ?? "Generated \(policyId)"
  let exerciseRange = gRange(availability["exercisesPerSession"])
  let minimumExercises = Int(exerciseRange.min ?? 1)
  let maximumExercises = exerciseRange.max.map { Int($0) }
  var sessions: [[String: JSONValue]] = offsets.enumerated().map { index, offset in
    let kind = gString(policy["splitStrategy"]) == "upper_lower_alternating" ? (index % 2 == 0 ? "Upper" : "Lower") : "Session"
    let name = kind == "Session" ? "Session \(index + 1)" : "\(kind) \(index / 2 + 1)"
    return ["planSessionId": .string("session-\(index + 1)"), "dayOffset": .number(Double(offset)), "name": .string(name), "exercises": .array([])]
  }
  var rationale: [String: Set<String>] = [:]
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
  func compatible(_ id: String, _ session: Int) -> Bool {
    guard gString(policy["splitStrategy"]) == "upper_lower_alternating", let exercise = candidateById[id] else { return true }
    let parameters = gObject(policy["parameters"]), prefix = session % 2 == 0 ? "upper" : "lower"
    let muscles = Set(gStringArray(parameters["\(prefix)Muscles"])), patterns = Set(gStringArray(parameters["\(prefix)Patterns"]))
    return !muscles.isDisjoint(with: Set(exercise.annotation.direct + exercise.annotation.indirect)) || !patterns.isDisjoint(with: Set(exercise.annotation.patterns))
  }
  if !lockedExerciseIds.isEmpty {
    guard currentPlan?.objectValue != nil else { return result("unsatisfiable", nil, nil, constraints: lockedExerciseIds.sorted().map { lockedConflict($0, "locked exercises require currentPlan") }) }
    for id in lockedExerciseIds.sorted() {
      guard let destination = sessions.firstIndex(where: { gNumber($0["dayOffset"]).map(Int.init) == lockedLocations[id]?.first }), compatible(id, destination) else { return result("unsatisfiable", nil, nil, constraints: [lockedConflict(id, "locked exercise is incompatible with generated split role")]) }
      add(id, destination, "LOCKED_EXERCISE")
    }
  }
  for familyId in requiredFamilies.sorted() {
    guard let candidate = ranked("family", familyId).first(where: { family($0.exerciseId) == familyId }) else { return result("unsatisfiable", nil, nil, constraints: [.object(["code": .string("NO_ELIGIBLE_FAMILY_EXERCISE"), "familyId": .string(familyId)])]) }
    guard let destination = sessions.indices.first(where: { compatible(candidate.exerciseId, $0) }) else { return result("unsatisfiable", nil, nil, constraints: [lockedConflict(nil, "required family is incompatible with generated split role")]) }
    add(candidate.exerciseId, destination, "REQUIRED_FAMILY")
  }
  for id in required.subtracting(Set(lockedExerciseIds)).sorted() {
    guard let destination = sessions.indices.first(where: { compatible(id, $0) }) else { return result("unsatisfiable", nil, nil, constraints: [.object(["code": .string("NO_ELIGIBLE_EXERCISE"), "exerciseId": .string(id), "detail": .string("required exercise incompatible with split")])]) }
    add(id, destination, "REQUIRED_EXERCISE")
  }
  func allocationDeficits(_ evaluation: JSONValue, _ phase: String) -> [(Double, String, String)] {
    let root = gObject(evaluation), sections: [(String, [String: JSONValue], String)] = [
      ("muscle", gObject(root["muscleCoverage"]), "actualEffectiveSets"),
      ("frequency", gObject(root["frequency"]), "normalizedExposuresPer7Days"),
      ("pattern", gObject(root["movementPatterns"]), "plannedSets"),
      ("family", gObject(gObject(root["families"])["targets"]), "plannedSets")
    ]
    var result: [(Double, String, String)] = []
    for (kind, rows, actualKey) in sections {
      for (key, raw) in rows {
        let row = gObject(raw), actual = gNumber(row[actualKey]) ?? 0
        let required = phase == "minimum" ? gNumber(row["minimum"]) : gNumber(row["target"])
        if let required, actual < required { result.append((required - actual, kind, key)) }
      }
    }
    return result.sorted { lhs, rhs in
      if lhs.0 != rhs.0 { return lhs.0 > rhs.0 }
      if lhs.1 != rhs.1 { return lhs.1 < rhs.1 }
      return lhs.2 < rhs.2
    }
  }
  func exceedsMaximum(_ evaluation: JSONValue) -> Bool {
    let root = gObject(evaluation), sections = [gObject(root["muscleCoverage"]), gObject(root["frequency"]), gObject(root["movementPatterns"]), gObject(gObject(root["families"])["targets"])]
    return sections.contains { rows in rows.values.contains { row in
      let value = gObject(row), actual = gNumber(value["actualEffectiveSets"]) ?? gNumber(value["normalizedExposuresPer7Days"]) ?? gNumber(value["plannedSets"]) ?? 0
      return (gNumber(value["maximum"]) ?? .infinity) < actual
    } }
  }
  let initialPlan: JSONValue = .object(["schemaVersion": .string("0.2.0"), "planId": .string(planId), "revisionId": .string(revisionId), "name": .string(planName), "description": .null, "cycle": .object(["lengthDays": .number(Double(cycle))]), "sessions": .array(sessions.map(JSONValue.object))])
  var allocationEvaluation = evaluatePlan(initialPlan, database: database, profile: profile, target: target, relationships: relationships)
  for phase in ["minimum", "target"] {
    var guardCount = 0
    while guardCount < 512, let deficit = allocationDeficits(allocationEvaluation, phase).first {
      guardCount += 1
      let eligible = ranked(deficit.1, deficit.2).filter { contribution($0, deficit.1, deficit.2) > 0 }
      var accepted = false
      for candidate in eligible {
        var choices = sessions.indices.filter { compatible(candidate.exerciseId, $0) }
        if deficit.1 == "frequency" {
          choices.sort { a, b in
            func exposed(_ index: Int) -> Int {
              gArray(sessions[index]["exercises"]).contains { raw in
                guard let exercise = candidateById[gString(gObject(raw)["exerciseId"]) ?? ""] else { return false }
                return contribution(exercise, "frequency", deficit.2) > 0
              } ? 1 : 0
            }
            let left = exposed(a), right = exposed(b)
            return left == right ? (gArray(sessions[a]["exercises"]).count, a) < (gArray(sessions[b]["exercises"]).count, b) : left < right
          }
        } else { choices.sort { a, b in let left = gArray(sessions[a]["exercises"]).count, right = gArray(sessions[b]["exercises"]).count; return left == right ? a < b : left < right } }
        for session in choices {
          if gArray(sessions[session]["exercises"]).contains(where: { family(gString(gObject($0)["exerciseId"]) ?? "") == family(candidate.exerciseId) && family(candidate.exerciseId) != nil }) { continue }
          var draftSessions = sessions
          var draft = gArray(draftSessions[session]["exercises"])
          let order = draft.count + 1, name = gString(candidateById[candidate.exerciseId]?.source?["name"]) ?? candidate.exerciseId
          draft.append(.object(["prescriptionId": .string(String(format: "rx-%02d-%02d", session + 1, order)), "exerciseId": .string(candidate.exerciseId), "exerciseName": .string(name), "order": .number(Double(order)), "sets": .number(1), "reps": reps, "effort": effort, "setType": .string("working")]))
          draftSessions[session]["exercises"] = .array(draft)
          let draftPlan: JSONValue = .object(["schemaVersion": .string("0.2.0"), "planId": .string(planId), "revisionId": .string(revisionId), "name": .string(planName), "description": .null, "cycle": .object(["lengthDays": .number(Double(cycle))]), "sessions": .array(draftSessions.map(JSONValue.object))])
          let evaluated = evaluatePlan(draftPlan, database: database, profile: profile, target: target, relationships: relationships)
          if !exceedsMaximum(evaluated) {
            sessions = draftSessions; allocationEvaluation = evaluated
            rationale[candidate.exerciseId, default: []].insert(deficit.1 == "frequency" ? "FREQUENCY_COVERAGE" : "TARGET_COVERAGE")
            accepted = true; break
          }
        }
        if accepted { break }
      }
      if !accepted { break }
    }
  }
  // Every generated session must satisfy the hard lower exercise bound. The
  // Python generator fills these slots only after target allocation, using
  // the same deterministic candidate order and maximum guard.
  for session in sessions.indices {
    while gArray(sessions[session]["exercises"]).count < minimumExercises {
      let existing = Set(gArray(sessions[session]["exercises"]).compactMap { gString(gObject($0)["exerciseId"]) })
      let choices = ranked("muscle", "").filter { !existing.contains($0.exerciseId) && compatible($0.exerciseId, session) && (maximumExercises == nil || gArray(sessions[session]["exercises"]).count < maximumExercises!) }
      guard let candidate = choices.first else {
        return result("unsatisfiable", nil, nil, constraints: [.object(["code": .string("NO_ELIGIBLE_EXERCISE"), "detail": .string("no eligible exercise for session \(session + 1)")])])
      }
      var draftSessions = sessions, exercises = gArray(draftSessions[session]["exercises"])
      let order = exercises.count + 1, name = gString(candidate.source?["name"]) ?? candidate.exerciseId
      exercises.append(.object(["prescriptionId": .string(String(format: "rx-%02d-%02d", session + 1, order)), "exerciseId": .string(candidate.exerciseId), "exerciseName": .string(name), "order": .number(Double(order)), "sets": .number(1), "reps": reps, "effort": effort, "setType": .string("working")]))
      draftSessions[session]["exercises"] = .array(exercises)
      let draftPlan: JSONValue = .object(["schemaVersion": .string("0.2.0"), "planId": .string(planId), "revisionId": .string(revisionId), "name": .string(planName), "description": .null, "cycle": .object(["lengthDays": .number(Double(cycle))]), "sessions": .array(draftSessions.map(JSONValue.object))])
      let evaluated = evaluatePlan(draftPlan, database: database, profile: profile, target: target, relationships: relationships)
      guard !exceedsMaximum(evaluated) else { return result("unsatisfiable", nil, evaluated, constraints: [.object(["code": .string("SESSION_COUNT_CONFLICT"), "detail": .string("cannot populate session without exceeding target maximum")])]) }
      sessions = draftSessions; allocationEvaluation = evaluated; rationale[candidate.exerciseId, default: []].insert("DETERMINISTIC_TIE_BREAK")
    }
  }
  let plan: JSONValue = .object(["schemaVersion": .string("0.2.0"), "planId": .string(planId), "revisionId": .string(revisionId), "name": .string(planName), "description": .null, "cycle": .object(["lengthDays": .number(Double(cycle))]), "sessions": .array(sessions.map(JSONValue.object))])
  let evaluation = evaluatePlan(plan, database: database, profile: profile, target: target, relationships: relationships)
  let typedPlanValid = (try? JSONDecoder().decode(WorkoutPlan.self, from: JSONEncoder().encode(plan))) != nil
  guard typedPlanValid else { return result("unsatisfiable", nil, evaluation, constraints: [.object(["code": .string("INVALID_GENERATED_PLAN")])], rationale: rationale.sorted { $0.key < $1.key }.map { .object(["exerciseId": .string($0.key), "reasonCodes": .array($0.value.sorted().map(JSONValue.string))]) }) }
  let hard = gObject(gObject(evaluation)["summary"])["satisfiesHardConstraints"] == .bool(true)
  let minimumGaps = allocationDeficits(evaluation, "minimum")
  let targetGaps = allocationDeficits(evaluation, "target")
  let targets = minimumGaps.map { deficit, kind, key in JSONValue.object(["code": .string("\(kind.uppercased())_TARGET_UNSATISFIED"), "targetId": .string(key), "deficit": .number(deficit)]) }
  let evalConstraints = gArray(gObject(gObject(evaluation)["constraints"])["violations"])
  let preferences = gObject(profileObject["exercisePreferences"])
  let selectedIds = Set(sessions.flatMap { gArray($0["exercises"]) }.compactMap { gString(gObject($0)["exerciseId"]) })
  let selectedFamilies = Set(selectedIds.compactMap(family))
  var soft: [JSONValue] = []
  let preferred = Set(gStringArray(preferences["preferredExerciseIds"])), preferredFamily = Set(gStringArray(preferences["preferredFamilyIds"]))
  let avoided = Set(gStringArray(preferences["avoidedExerciseIds"])), avoidedFamily = Set(gStringArray(preferences["avoidedFamilyIds"]))
  if !preferred.isEmpty && selectedIds.isDisjoint(with: preferred) { soft.append(.object(["code": .string("PREFERRED_EXERCISE_UNSATISFIED"), "exerciseIds": .array(preferred.sorted().map(JSONValue.string))])) }
  if !preferredFamily.isEmpty && selectedFamilies.isDisjoint(with: preferredFamily) { soft.append(.object(["code": .string("PREFERRED_FAMILY_UNSATISFIED"), "familyIds": .array(preferredFamily.sorted().map(JSONValue.string))])) }
  if !selectedIds.isDisjoint(with: avoided) { soft.append(.object(["code": .string("AVOIDED_EXERCISE_USED"), "exerciseIds": .array(selectedIds.intersection(avoided).sorted().map(JSONValue.string))])) }
  if !selectedFamilies.isDisjoint(with: avoidedFamily) { soft.append(.object(["code": .string("AVOIDED_FAMILY_USED"), "familyIds": .array(selectedFamilies.intersection(avoidedFamily).sorted().map(JSONValue.string))])) }
  let status = !hard ? "unsatisfiable" : (minimumGaps.isEmpty && targetGaps.isEmpty ? "generated" : "generated_with_target_gaps")
  return result(status, plan, evaluation, constraints: evalConstraints, targets: targets, soft: soft, rationale: rationale.sorted { $0.key < $1.key }.map { .object(["exerciseId": .string($0.key), "reasonCodes": .array($0.value.sorted().map(JSONValue.string))]) })
}
