import Foundation

private let progressionCountedTypes: Set<String> = ["working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"]

private func pObject(_ value: JSONValue?) -> [String: JSONValue] { value?.objectValue ?? [:] }
private func pNumber(_ value: JSONValue?) -> Double? { if case .number(let n)? = value { return n }; return nil }
private func pString(_ value: JSONValue?) -> String? { if case .string(let s)? = value { return s }; return nil }
private func pArray(_ value: JSONValue?) -> [JSONValue] { if case .array(let a)? = value { return a }; return [] }
private func pBefore(_ prescription: [String: JSONValue]) -> [String: JSONValue] { var result: [String: JSONValue] = [:]; for key in ["load", "reps", "sets"] { if let value = prescription[key] { result[key] = value } }; return result }
private func pRangeTop(_ value: JSONValue?) -> Double? { let object = pObject(value); return object["max"].flatMap(pNumber) ?? object["target"].flatMap(pNumber) ?? object["min"].flatMap(pNumber) ?? pNumber(value) }
private func pCountedSets(_ exercise: [String: JSONValue]) -> [[String: JSONValue]] { pArray(exercise["sets"]).compactMap { raw in let set = pObject(raw); guard set["completed"] == .bool(true) else { return nil }; if let type = pString(set["setType"]), !progressionCountedTypes.contains(type) { return nil }; return set } }
private func pDecision(_ policyId: String, _ type: String, _ prescription: [String: JSONValue], _ state: [String: JSONValue], _ reasons: Set<String>, after: [String: JSONValue]? = nil, evidence: [String: JSONValue] = [:]) -> JSONValue {
  let policyVersion = "1.0.0", context = pObject(state["planContext"])
  return .object(["schemaVersion": .string("0.1.0"), "decisionType": .string(type), "policyId": .string(policyId), "policyVersion": .string(policyVersion), "planId": context["planId"] ?? state["planId"] ?? .null, "revisionId": context["revisionId"] ?? state["revisionId"] ?? .null, "prescriptionId": prescription["prescriptionId"] ?? .null, "exerciseId": prescription["exerciseId"] ?? .null, "before": .object(pBefore(prescription)), "after": .object(after ?? pBefore(prescription)), "reasonCodes": .array(reasons.sorted().map(JSONValue.string)), "evidence": .object(evidence), "provenance": context["provenance"] ?? state["provenance"] ?? .object([:])])
}

public func applyProgressionPolicy(_ policy: String, prescription value: JSONValue, exerciseState stateValue: JSONValue, parameters parametersValue: JSONValue? = nil) -> JSONValue {
  let prescription = pObject(value), state = pObject(stateValue), parameters = pObject(parametersValue)
  guard policy == "hold-v1" || policy == "double-progression-v1" else { return pDecision(policy, "insufficient_data", prescription, state, ["NO_RECENT_PERFORMANCE"]) }
  if policy == "hold-v1" { return pDecision(policy, "hold", prescription, state, ["POLICY_HOLD"]) }
  guard let actual = state["lastActual"].flatMap({ $0.objectValue }) else { return pDecision(policy, "insufficient_data", prescription, state, ["NO_MATCHED_ACTUAL", "NO_RECENT_PERFORMANCE"]) }
  let plannedItems = pArray(prescription["plannedSets"]).compactMap { raw -> [String: JSONValue]? in let item = pObject(raw); guard progressionCountedTypes.contains(pString(item["setType"]) ?? "") else { return nil }; return item }
  let required = plannedItems.isEmpty ? Int(pRangeTop(prescription["sets"]) ?? 0) : plannedItems.count
  let sets = pCountedSets(actual)
  if sets.count < required { return pDecision(policy, "hold", prescription, state, ["SET_TARGET_NOT_COMPLETED", "INCOMPLETE_WORKOUT"], evidence: ["plannedSetCount": .number(Double(required)), "actualSetCount": .number(Double(sets.count))]) }
  let comparisons: [JSONValue] = sets.prefix(required).enumerated().map { index, set in
    let planned = plannedItems.indices.contains(index) ? plannedItems[index]["reps"] : prescription["reps"]
    return .object(["setId": set["setPrescriptionId"] ?? set["setNumber"] ?? .null, "plannedReps": planned ?? .null, "actualReps": set["reps"] ?? .null])
  }
  let topReached = comparisons.allSatisfy { pNumber($0.objectValue?["actualReps"]) != nil && pRangeTop($0.objectValue?["plannedReps"]) != nil && pNumber($0.objectValue?["actualReps"])! >= pRangeTop($0.objectValue?["plannedReps"])! }
  if !topReached { return pDecision(policy, "hold", prescription, state, ["REP_TARGET_NOT_ACHIEVED"], evidence: ["sets": .array(comparisons)]) }
  var reasons: Set<String> = ["REP_TARGET_ACHIEVED"]
  let effort = pObject(prescription["effort"]), effortKey = effort["rir"] != nil ? "rir" : (effort["rpe"] != nil ? "rpe" : nil)
  if let effortKey {
    let actualEffort = sets.prefix(required).compactMap { pNumber($0[effortKey]) }
    guard actualEffort.count == required else { return pDecision(policy, "insufficient_data", prescription, state, ["INSUFFICIENT_EFFORT_DATA"], evidence: ["sets": .array(comparisons), "effortType": .string(effortKey)]) }
    let bounds = pObject(effort[effortKey]); let low = pRangeTop(.object(bounds)), high = bounds["max"].flatMap(pNumber) ?? bounds["target"].flatMap(pNumber)
    var effortReasons = Set<String>()
    for actual in actualEffort { if effortKey == "rpe", let low, actual < low { effortReasons.insert("EFFORT_TOO_LOW") }; if effortKey == "rpe", let high, actual > high { effortReasons.insert("EFFORT_TOO_HIGH") }; if effortKey == "rir", let low, actual < low { effortReasons.insert("EFFORT_TOO_HIGH") }; if effortKey == "rir", let high, actual > high { effortReasons.insert("EFFORT_TOO_LOW") } }
    if !effortReasons.isEmpty { return pDecision(policy, "hold", prescription, state, effortReasons, evidence: ["sets": .array(comparisons), "actualEffort": .array(actualEffort.map(JSONValue.number))]) }
    reasons.insert("EFFORT_WITHIN_TARGET")
  }
  guard let load = prescription["load"].flatMap({ $0.objectValue }), let loadValue = pNumber(load["value"]) ?? pNumber(load["target"]) else { return pDecision(policy, "insufficient_data", prescription, state, ["INSUFFICIENT_LOAD_DATA"], evidence: ["sets": .array(comparisons)]) }
  guard let increment = parameters["loadIncrement"].flatMap({ $0.objectValue }), let incrementValue = pNumber(increment["value"]), incrementValue > 0, let unit = pString(load["unit"]), let incrementUnit = pString(increment["unit"]) else { return pDecision(policy, "insufficient_data", prescription, state, ["INSUFFICIENT_LOAD_DATA"], evidence: ["sets": .array(comparisons)]) }
  func kilograms(_ value: Double, _ unit: String) -> Double? { switch unit.lowercased() { case "kg": return value; case "lb": return value * 0.45359237; case "g": return value / 1000; default: return nil } }
  guard let currentKg = kilograms(loadValue, unit), let incrementKg = kilograms(incrementValue, incrementUnit) else { return pDecision(policy, "insufficient_data", prescription, state, ["INCOMPATIBLE_LOAD_UNIT"], evidence: ["sets": .array(comparisons)]) }
  let newKg = currentKg + incrementKg
  let newValue: Double = unit.lowercased() == "kg" ? newKg : (unit.lowercased() == "lb" ? newKg / 0.45359237 : newKg * 1000)
  var after = pBefore(prescription); after["load"] = .object(["unit": .string(unit), "value": .number((newValue * 1_000_000).rounded() / 1_000_000)])
  return pDecision(policy, "increase_load", prescription, state, reasons, after: after, evidence: ["sets": .array(comparisons), "previousLoad": .object(load), "newLoad": after["load"]!])
}
