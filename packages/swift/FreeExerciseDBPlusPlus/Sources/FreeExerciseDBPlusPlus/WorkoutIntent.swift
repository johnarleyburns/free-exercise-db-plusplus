import Foundation

public struct IntRange: Codable, Sendable, Equatable {
  public var min: Int?
  public var target: Int?
  public var max: Int?
  public init(min: Int? = nil, target: Int? = nil, max: Int? = nil) {
    self.min = min
    self.target = target
    self.max = max
  }
}
public struct WorkoutSchedule: Codable, Sendable, Equatable {
  public var cycleLengthDays: Int?
  public var sessionsPerCycle: IntRange?
  public var preferredDayOffsets: [Int]
  public var excludedDayOffsets: [Int]
  public var preferredWeekdays: [String]
  public var excludedWeekdays: [String]
  public init(
    cycleLengthDays: Int? = nil, sessionsPerCycle: IntRange? = nil, preferredDayOffsets: [Int] = [],
    excludedDayOffsets: [Int] = [], preferredWeekdays: [String] = [],
    excludedWeekdays: [String] = []
  ) {
    self.cycleLengthDays = cycleLengthDays
    self.sessionsPerCycle = sessionsPerCycle
    self.preferredDayOffsets = preferredDayOffsets
    self.excludedDayOffsets = excludedDayOffsets
    self.preferredWeekdays = preferredWeekdays
    self.excludedWeekdays = excludedWeekdays
  }
}
public struct SessionConstraints: Codable, Sendable, Equatable {
  public var exercisesPerSession: IntRange?
  public init(exercisesPerSession: IntRange? = nil) {
    self.exercisesPerSession = exercisesPerSession
  }
}
public struct ExerciseConstraints: Codable, Sendable, Equatable {
  public var requiredExerciseIds: [String]
  public var lockedExerciseIds: [String]
  public var excludedExerciseIds: [String]
  public var requiredFamilyIds: [String]
  public var excludedFamilyIds: [String]
  public init(
    requiredExerciseIds: [String] = [], lockedExerciseIds: [String] = [],
    excludedExerciseIds: [String] = [], requiredFamilyIds: [String] = [],
    excludedFamilyIds: [String] = []
  ) {
    self.requiredExerciseIds = requiredExerciseIds
    self.lockedExerciseIds = lockedExerciseIds
    self.excludedExerciseIds = excludedExerciseIds
    self.requiredFamilyIds = requiredFamilyIds
    self.excludedFamilyIds = excludedFamilyIds
  }
}
public struct WorkoutPreferences: Codable, Sendable, Equatable {
  public var preferredExerciseIds: [String]
  public var avoidedExerciseIds: [String]
  public var preferredFamilyIds: [String]
  public var avoidedFamilyIds: [String]
  public init(
    preferredExerciseIds: [String] = [], avoidedExerciseIds: [String] = [],
    preferredFamilyIds: [String] = [], avoidedFamilyIds: [String] = []
  ) {
    self.preferredExerciseIds = preferredExerciseIds
    self.avoidedExerciseIds = avoidedExerciseIds
    self.preferredFamilyIds = preferredFamilyIds
    self.avoidedFamilyIds = avoidedFamilyIds
  }
}
public struct EquipmentOverrides: Codable, Sendable, Equatable {
  public var addEquipment: [String]
  public var removeEquipment: [String]
  public init(addEquipment: [String] = [], removeEquipment: [String] = []) {
    self.addEquipment = addEquipment
    self.removeEquipment = removeEquipment
  }
}
public struct WorkoutIntent: Codable, Sendable, Equatable {
  public var schemaVersion: String
  public var intentId: String?
  public var subjectId: String?
  public var goal: String?
  public var requestedGoalPolicy: String?
  public var requestedPlanningPolicy: String?
  public var environment: String?
  public var schedule: WorkoutSchedule?
  public var sessionConstraints: SessionConstraints?
  public var exerciseConstraints: ExerciseConstraints?
  public var preferences: WorkoutPreferences?
  public var equipmentOverrides: EquipmentOverrides?
  public var continuity: String?
  public var useHistory: Bool?
  public var historyWindow: String?
  public init(
    schemaVersion: String = "0.1.0", intentId: String? = nil, subjectId: String? = nil,
    goal: String? = nil, requestedGoalPolicy: String? = nil, requestedPlanningPolicy: String? = nil,
    environment: String? = nil, schedule: WorkoutSchedule? = nil,
    sessionConstraints: SessionConstraints? = nil, exerciseConstraints: ExerciseConstraints? = nil,
    preferences: WorkoutPreferences? = nil, equipmentOverrides: EquipmentOverrides? = nil,
    continuity: String? = nil, useHistory: Bool? = nil, historyWindow: String? = nil
  ) {
    self.schemaVersion = schemaVersion
    self.intentId = intentId
    self.subjectId = subjectId
    self.goal = goal
    self.requestedGoalPolicy = requestedGoalPolicy
    self.requestedPlanningPolicy = requestedPlanningPolicy
    self.environment = environment
    self.schedule = schedule
    self.sessionConstraints = sessionConstraints
    self.exerciseConstraints = exerciseConstraints
    self.preferences = preferences
    self.equipmentOverrides = equipmentOverrides
    self.continuity = continuity
    self.useHistory = useHistory
    self.historyWindow = historyWindow
  }
}
extension WorkoutIntent {
  private enum CodingKeys: String, CodingKey { case schemaVersion, intentId, subjectId, goal, requestedGoalPolicy, requestedPlanningPolicy, environment, schedule, sessionConstraints, exerciseConstraints, preferences, equipmentOverrides, continuity, useHistory, historyWindow }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    guard c.contains(.schemaVersion) else { throw DecodingError.keyNotFound(CodingKeys.schemaVersion, .init(codingPath: decoder.codingPath, debugDescription: "schemaVersion is required")) }
    schemaVersion = try c.decode(String.self, forKey: .schemaVersion)
    intentId = try c.decodeIfPresent(String.self, forKey: .intentId); subjectId = try c.decodeIfPresent(String.self, forKey: .subjectId)
    goal = try c.decodeIfPresent(String.self, forKey: .goal); requestedGoalPolicy = try c.decodeIfPresent(String.self, forKey: .requestedGoalPolicy); requestedPlanningPolicy = try c.decodeIfPresent(String.self, forKey: .requestedPlanningPolicy)
    environment = try c.decodeIfPresent(String.self, forKey: .environment); schedule = try c.decodeIfPresent(WorkoutSchedule.self, forKey: .schedule); sessionConstraints = try c.decodeIfPresent(SessionConstraints.self, forKey: .sessionConstraints); exerciseConstraints = try c.decodeIfPresent(ExerciseConstraints.self, forKey: .exerciseConstraints); preferences = try c.decodeIfPresent(WorkoutPreferences.self, forKey: .preferences); equipmentOverrides = try c.decodeIfPresent(EquipmentOverrides.self, forKey: .equipmentOverrides); continuity = try c.decodeIfPresent(String.self, forKey: .continuity); useHistory = try c.decodeIfPresent(Bool.self, forKey: .useHistory); historyWindow = try c.decodeIfPresent(String.self, forKey: .historyWindow)
  }
}
extension WorkoutSchedule {
  private enum CodingKeys: String, CodingKey {
    case cycleLengthDays, sessionsPerCycle, preferredDayOffsets, excludedDayOffsets,
      preferredWeekdays, excludedWeekdays
  }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    cycleLengthDays = try c.decodeIfPresent(Int.self, forKey: .cycleLengthDays)
    sessionsPerCycle = try c.decodeIfPresent(IntRange.self, forKey: .sessionsPerCycle)
    preferredDayOffsets = try c.decodeIfPresent([Int].self, forKey: .preferredDayOffsets) ?? []
    excludedDayOffsets = try c.decodeIfPresent([Int].self, forKey: .excludedDayOffsets) ?? []
    preferredWeekdays = try c.decodeIfPresent([String].self, forKey: .preferredWeekdays) ?? []
    excludedWeekdays = try c.decodeIfPresent([String].self, forKey: .excludedWeekdays) ?? []
  }
}
extension ExerciseConstraints {
  private enum CodingKeys: String, CodingKey {
    case requiredExerciseIds, lockedExerciseIds, excludedExerciseIds, requiredFamilyIds,
      excludedFamilyIds
  }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    requiredExerciseIds = try c.decodeIfPresent([String].self, forKey: .requiredExerciseIds) ?? []
    lockedExerciseIds = try c.decodeIfPresent([String].self, forKey: .lockedExerciseIds) ?? []
    excludedExerciseIds = try c.decodeIfPresent([String].self, forKey: .excludedExerciseIds) ?? []
    requiredFamilyIds = try c.decodeIfPresent([String].self, forKey: .requiredFamilyIds) ?? []
    excludedFamilyIds = try c.decodeIfPresent([String].self, forKey: .excludedFamilyIds) ?? []
  }
}
extension WorkoutPreferences {
  private enum CodingKeys: String, CodingKey {
    case preferredExerciseIds, avoidedExerciseIds, preferredFamilyIds, avoidedFamilyIds
  }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    preferredExerciseIds = try c.decodeIfPresent([String].self, forKey: .preferredExerciseIds) ?? []
    avoidedExerciseIds = try c.decodeIfPresent([String].self, forKey: .avoidedExerciseIds) ?? []
    preferredFamilyIds = try c.decodeIfPresent([String].self, forKey: .preferredFamilyIds) ?? []
    avoidedFamilyIds = try c.decodeIfPresent([String].self, forKey: .avoidedFamilyIds) ?? []
  }
}
extension EquipmentOverrides {
  private enum CodingKeys: String, CodingKey { case addEquipment, removeEquipment }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    addEquipment = try c.decodeIfPresent([String].self, forKey: .addEquipment) ?? []
    removeEquipment = try c.decodeIfPresent([String].self, forKey: .removeEquipment) ?? []
  }
}
public struct ExplicitOverrides: Codable, Sendable, Equatable {
  public var goalPolicy: Bool
  public var planningPolicy: Bool
  public var target: Bool
  public var trainingProfile: Bool
  public var equipmentAdded: [String]
  public var equipmentRemoved: [String]
  public init(
    goalPolicy: Bool = false, planningPolicy: Bool = false, target: Bool = false,
    trainingProfile: Bool = false, equipmentAdded: [String] = [], equipmentRemoved: [String] = []
  ) {
    self.goalPolicy = goalPolicy
    self.planningPolicy = planningPolicy
    self.target = target
    self.trainingProfile = trainingProfile
    self.equipmentAdded = Array(Set(equipmentAdded)).sorted()
    self.equipmentRemoved = Array(Set(equipmentRemoved)).sorted()
  }
}
public struct GoalPolicyReference: Codable, Sendable, Equatable {
  public let policyId: String
  public let policyVersion: String
  public let description: String?
  public init(policyId: String, policyVersion: String = "1", description: String? = nil) {
    self.policyId = policyId
    self.policyVersion = policyVersion
    self.description = description
  }
}
public struct IntentConflict: Codable, Sendable, Equatable {
  public let code: String
  public let detail: String?
  public let goal: String?
  public let requestedGoalPolicy: String?
  public let policyGoal: String?
  public let exerciseId: String?
  public let familyId: String?
  public init(
    code: String, detail: String? = nil, goal: String? = nil, requestedGoalPolicy: String? = nil,
    policyGoal: String? = nil, exerciseId: String? = nil, familyId: String? = nil
  ) {
    self.code = code
    self.detail = detail
    self.goal = goal
    self.requestedGoalPolicy = requestedGoalPolicy
    self.policyGoal = policyGoal
    self.exerciseId = exerciseId
    self.familyId = familyId
  }
}
public struct MissingInformation: Codable, Sendable, Equatable {
  public let field: String
  public let reason: String
  public init(field: String, reason: String) {
    self.field = field
    self.reason = reason
  }
}
public struct IntentResolutionResult: Codable, Sendable, Equatable {
  public let status: String
  public let resolvedProfile: JSONValue?
  public let resolvedTarget: JSONValue?
  public let planningPolicy: String?
  public let goalPolicy: GoalPolicyReference?
  public let environmentPolicy: String?
  public let generationOptions: JSONValue
  public let missingInformation: [MissingInformation]
  public let warnings: [String]
  public let conflicts: [IntentConflict]
  public let defaultsApplied: [String]
  public let explicitOverrides: ExplicitOverrides
  public let provenance: [String: JSONValue]
  public init(
    status: String, resolvedProfile: JSONValue? = nil, resolvedTarget: JSONValue? = nil,
    planningPolicy: String? = nil, goalPolicy: GoalPolicyReference? = nil,
    environmentPolicy: String? = nil, generationOptions: JSONValue = .object([:]),
    missingInformation: [MissingInformation] = [], warnings: [String] = [],
    conflicts: [IntentConflict] = [], defaultsApplied: [String] = [],
    explicitOverrides: ExplicitOverrides = ExplicitOverrides(),
    provenance: [String: JSONValue] = [:]
  ) {
    self.status = status
    self.resolvedProfile = resolvedProfile
    self.resolvedTarget = resolvedTarget
    self.planningPolicy = planningPolicy
    self.goalPolicy = goalPolicy
    self.environmentPolicy = environmentPolicy
    self.generationOptions = generationOptions
    self.missingInformation = missingInformation
    self.warnings = warnings
    self.conflicts = conflicts
    self.defaultsApplied = defaultsApplied
    self.explicitOverrides = explicitOverrides
    self.provenance = provenance
  }
  private enum CodingKeys: String, CodingKey { case status, resolvedProfile, resolvedTarget, planningPolicy, goalPolicy, environmentPolicy, generationOptions, missingInformation, warnings, conflicts, defaultsApplied, explicitOverrides, provenance }
  public func encode(to encoder: Encoder) throws {
    var c = encoder.container(keyedBy: CodingKeys.self)
    try c.encode(status, forKey: .status); try c.encode(resolvedProfile, forKey: .resolvedProfile); try c.encode(resolvedTarget, forKey: .resolvedTarget); try c.encode(planningPolicy, forKey: .planningPolicy); try c.encode(goalPolicy, forKey: .goalPolicy); try c.encode(environmentPolicy, forKey: .environmentPolicy); try c.encode(generationOptions, forKey: .generationOptions); try c.encode(missingInformation, forKey: .missingInformation); try c.encode(warnings, forKey: .warnings); try c.encode(conflicts, forKey: .conflicts); try c.encode(defaultsApplied, forKey: .defaultsApplied); try c.encode(explicitOverrides, forKey: .explicitOverrides); try c.encode(provenance, forKey: .provenance)
  }
}

extension JSONValue {
  fileprivate var arrayValues: [JSONValue] {
    if case .array(let x) = self { return x }
    return []
  }
  fileprivate var stringValue: String? {
    if case .string(let x) = self { return x }
    return nil
  }
  fileprivate var numberValue: Double? {
    if case .number(let x) = self { return x }
    return nil
  }
}
private func o(_ x: JSONValue?) -> [String: JSONValue] { x?.objectValue ?? [:] }
private func s(_ x: Int) -> JSONValue { .number(Double(x)) }
private func s(_ x: String) -> JSONValue { .string(x) }
private func rangeJSON(_ x: IntRange) -> JSONValue {
  var r: [String: JSONValue] = [:]
  if let v = x.min { r["min"] = s(v) }
  if let v = x.target { r["target"] = s(v) }
  if let v = x.max { r["max"] = s(v) }
  return .object(r)
}
public enum IntentValidator {
  public static let weekdays = [
    "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday",
  ]
  public static func validate(_ x: WorkoutIntent, database: FEDatabase? = nil, relationships: ExerciseRelationships? = nil) -> [String] {
    var e: [String] = []
    if x.schemaVersion != "0.1.0" { e += ["schemaVersion: must be 0.1.0"] }
    let a = x.schedule?.preferredWeekdays ?? []
    let b = x.schedule?.excludedWeekdays ?? []
    if !(a + b).isEmpty && x.schedule?.cycleLengthDays != 7 {
      e += ["schedule weekday fields require cycleLengthDays of 7"]
    }
    if !Set(a).isDisjoint(with: Set(b)) {
      e += ["schedule: preferredWeekdays and excludedWeekdays conflict"]
    }
    let pa = x.schedule?.preferredDayOffsets ?? []
    let pb = x.schedule?.excludedDayOffsets ?? []
    if !Set(pa).isDisjoint(with: Set(pb)) {
      e += ["schedule: preferredDayOffsets and excludedDayOffsets conflict"]
    }
    if let c = x.schedule?.cycleLengthDays, (pa + pb).contains(where: { $0 < 0 || $0 >= c }) {
      e += ["schedule day offsets must be within cycleLengthDays"]
    }
    if let c = x.schedule?.cycleLengthDays, c < 1 { e += ["schedule.cycleLengthDays: must be at least 1"] }
    if let r = x.schedule?.sessionsPerCycle, [r.min, r.target, r.max].compactMap({ $0 }).contains(where: { $0 < 0 }) { e += ["schedule.sessionsPerCycle: values must be non-negative"] }
    if let r = x.sessionConstraints?.exercisesPerSession, [r.min, r.target, r.max].compactMap({ $0 }).contains(where: { $0 < 0 }) { e += ["sessionConstraints.exercisesPerSession: values must be non-negative"] }
    if Set(x.schedule?.preferredWeekdays ?? []).count != (x.schedule?.preferredWeekdays ?? []).count { e += ["schedule.preferredWeekdays: duplicate values"] }
    if Set(x.schedule?.excludedWeekdays ?? []).count != (x.schedule?.excludedWeekdays ?? []).count { e += ["schedule.excludedWeekdays: duplicate values"] }
    if Set(x.schedule?.preferredDayOffsets ?? []).count != (x.schedule?.preferredDayOffsets ?? []).count { e += ["schedule.preferredDayOffsets: duplicate values"] }
    if Set(x.schedule?.excludedDayOffsets ?? []).count != (x.schedule?.excludedDayOffsets ?? []).count { e += ["schedule.excludedDayOffsets: duplicate values"] }
    if let r = x.schedule?.sessionsPerCycle { e += ranges(r, "schedule.sessionsPerCycle") }
    if let r = x.sessionConstraints?.exercisesPerSession {
      e += ranges(r, "sessionConstraints.exercisesPerSession")
    }
    if let c = x.exerciseConstraints,
      !Set(c.requiredExerciseIds + c.lockedExerciseIds).isDisjoint(with: Set(c.excludedExerciseIds))
    {
      e += ["exerciseConstraints: requiredExerciseIds conflicts with excludedExerciseIds"]
    }
    if let c = x.exerciseConstraints,
      !Set(c.requiredFamilyIds).isDisjoint(with: Set(c.excludedFamilyIds))
    {
      e += ["exerciseConstraints: requiredFamilyIds conflicts with excludedFamilyIds"]
    }
    if let p = x.preferences, let c = x.exerciseConstraints {
      if !Set(p.preferredExerciseIds).isDisjoint(with: Set(c.excludedExerciseIds)) { e += ["preferences: preferredExerciseIds conflicts with excludedExerciseIds"] }
      if !Set(p.avoidedExerciseIds).isDisjoint(with: Set(c.excludedExerciseIds)) { e += ["preferences: avoidedExerciseIds conflicts with excludedExerciseIds"] }
      if !Set(p.preferredFamilyIds).isDisjoint(with: Set(c.excludedFamilyIds)) { e += ["preferences: preferredFamilyIds conflicts with excludedFamilyIds"] }
      if !Set(p.avoidedFamilyIds).isDisjoint(with: Set(c.excludedFamilyIds)) { e += ["preferences: avoidedFamilyIds conflicts with excludedFamilyIds"] }
    }
    if x.requestedGoalPolicy == "general-strength-v1" && x.goal == "hypertrophy"
      || x.requestedGoalPolicy == "general-hypertrophy-v1" && x.goal == "strength"
    {
      e += ["GOAL_POLICY_MISMATCH"]
    }
    if let goal = x.goal, !["hypertrophy", "strength", "muscular_endurance", "general_fitness", "skill_practice", "power"].contains(goal) { e += ["goal: unsupported value"] }
    if let environment = x.environment, !["commercial_gym", "home_gym", "minimal_equipment", "bodyweight_only", "custom"].contains(environment) { e += ["environment: unsupported value"] }
    if let continuity = x.continuity, !["preserve", "neutral", "vary"].contains(continuity) { e += ["continuity: unsupported value"] }
    if let policy = x.requestedPlanningPolicy,
      !["full-body-general-v1", "upper-lower-general-v1"].contains(policy)
    {
      e += ["requestedPlanningPolicy: unknown planning policy"]
    }
    let constraints = x.exerciseConstraints
    let preferences = x.preferences
    let familyValues = (constraints?.requiredFamilyIds ?? []) + (constraints?.excludedFamilyIds ?? []) + (preferences?.preferredFamilyIds ?? []) + (preferences?.avoidedFamilyIds ?? [])
    if !familyValues.isEmpty && relationships == nil { e += ["exercise family constraints require exercise relationships"] }
    if let database {
      let exerciseIDs = Set(database.exerciseIDs)
      for (field, values) in [
        ("requiredExerciseIds", constraints?.requiredExerciseIds ?? []),
        ("lockedExerciseIds", constraints?.lockedExerciseIds ?? []),
        ("excludedExerciseIds", constraints?.excludedExerciseIds ?? []),
        ("preferredExerciseIds", preferences?.preferredExerciseIds ?? []),
        ("avoidedExerciseIds", preferences?.avoidedExerciseIds ?? [])
      ] { for value in values where !exerciseIDs.contains(value) { e += ["\(field): unknown exerciseId: \(value)"] } }
      let equipment = x.equipmentOverrides
      for (field, values) in [("addEquipment", equipment?.addEquipment ?? []), ("removeEquipment", equipment?.removeEquipment ?? [])] {
        for value in values where !database.equipmentVocabulary.contains(value) { e += ["equipmentOverrides.\(field): unknown DB++ equipment value: \(value)"] }
      }
      if let relationships {
        let familyIDs = Set(relationships.families.keys)
        for (field, values) in [("requiredFamilyIds", constraints?.requiredFamilyIds ?? []), ("excludedFamilyIds", constraints?.excludedFamilyIds ?? []), ("preferredFamilyIds", preferences?.preferredFamilyIds ?? []), ("avoidedFamilyIds", preferences?.avoidedFamilyIds ?? [])] {
          for value in values where !familyIDs.contains(value) { e += ["\(field): unknown familyId: \(value)"] }
        }
      }
    }
    return Array(Set(e)).sorted()
  }
  private static func ranges(_ r: IntRange, _ p: String) -> [String] {
    var e: [String] = []
    if let a = r.min, let b = r.max, a > b { e += ["\(p): min must not exceed max"] }
    if let a = r.min, let b = r.target, b < a { e += ["\(p): target must not be below min"] }
    if let a = r.max, let b = r.target, b > a { e += ["\(p): target must not exceed max"] }
    return e
  }
}

private func merge(_ base: JSONValue, _ explicit: JSONValue?) -> JSONValue {
  guard case .object(var r) = base, case .object(let e)? = explicit else { return explicit ?? base }
  func m(_ a: JSONValue?, _ b: JSONValue) -> JSONValue {
    guard case .object(let x) = a, case .object(let y) = b else { return b }
    return .object(x.merging(y) { m($0, $1) })
  }
  for (k, v) in e {
    if ["muscles", "movementPatterns", "families"].contains(k) {
      r[k] = m(r[k], v)
    } else if k == "frequency", case .object(let f) = v {
      var q = o(r[k])
      q["muscles"] = m(q["muscles"], f["muscles"] ?? .object([:]))
      r[k] = .object(q)
    } else {
      r[k] = v
    }
  }
  return .object(r)
}

private enum IntentPolicyCatalog {
  static let root: [String: JSONValue] = {
    guard let url = Bundle.module.url(forResource: "intent-policies", withExtension: "json"),
      let data = try? Data(contentsOf: url),
      let value = try? JSONDecoder().decode(JSONValue.self, from: data),
      case .object(let object) = value else { return [:] }
    return object
  }()
  static var goals: [String: JSONValue] { o(root["goalPolicies"]) }
  static var environments: [String: JSONValue] { o(root["environmentPolicies"]) }
}

public func deriveTrainingState(_ history: JSONValue, asOf: String) -> JSONValue {
  let root = history.objectValue ?? [:]
  let plans = (root["plans"]?.arrayValues ?? []).compactMap { $0.objectValue }
  let activations = (root["planActivations"]?.arrayValues ?? []).compactMap { $0.objectValue }
  func parseTimestamp(_ value: String) -> Date? {
    let formatter = ISO8601DateFormatter()
    formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
    if let date = formatter.date(from: value) { return date }
    formatter.formatOptions = [.withInternetDateTime]
    return formatter.date(from: value)
  }
  let asOfInstant = parseTimestamp(asOf)
  let activePair = activations.compactMap { activation -> (plan: [String: JSONValue], activation: [String: JSONValue], date: Date)? in
    guard let from = activation["effectiveFrom"]?.stringValue,
      let fromDate = parseTimestamp(from), let asOfInstant,
      fromDate <= asOfInstant,
      activation["effectiveTo"]?.stringValue.map({ parseTimestamp($0).map { asOfInstant < $0 } ?? false }) ?? true,
      let plan = plans.first(where: { $0["planId"] == activation["planId"] && $0["revisionId"] == activation["revisionId"] })
    else { return nil }
    return (plan: plan, activation: activation, date: fromDate)
  }.max { $0.date < $1.date }
  let active = activePair?.plan
  let asOfDate = String(asOf.prefix(10))
  let calendar = Calendar(identifier: .gregorian)
  let formatter = ISO8601DateFormatter()
  let lowerDate = formatter.date(from: "\(asOfDate)T00:00:00Z").flatMap { calendar.date(byAdding: .day, value: -27, to: $0) }.map { String(formatter.string(from: $0).prefix(10)) } ?? asOfDate
  let workouts = (root["workouts"]?.arrayValues ?? []).compactMap { $0.objectValue }.filter {
    let stamp = $0["startTime"]?.stringValue ?? ""
    guard let instant = parseTimestamp(stamp), let asOfInstant else { return false }
    return String(stamp.prefix(10)) >= lowerDate && instant <= asOfInstant
  }
  var exerciseState: [String: JSONValue] = [:]
  for workout in workouts { for raw in workout["exercises"]?.arrayValues ?? [] { guard let exercise = raw.objectValue, let id = exercise["exerciseId"]?.stringValue else { continue }; let count = exercise["sets"]?.arrayValues.filter { $0.objectValue?["completed"] == .bool(true) }.count ?? 0; let previous = exerciseState[id]?.objectValue ?? [:]; exerciseState[id] = .object(["exerciseId": .string(id), "recentSessionCount": .number((previous["recentSessionCount"]?.numberValue ?? 0) + 1), "recentCompletedSetCount": .number((previous["recentCompletedSetCount"]?.numberValue ?? 0) + Double(count))]) } }
  var activePlan: [String: JSONValue] = [:]
  if let active, let activation = activePair?.activation, let from = activation["effectiveFrom"]?.stringValue {
    let cycle = Int(active["cycle"]?.objectValue?["lengthDays"]?.numberValue ?? 7); let fromDate = String(from.prefix(10)); let elapsed = max(0, (formatter.date(from: "\(asOfDate)T00:00:00Z")?.timeIntervalSince(formatter.date(from: "\(fromDate)T00:00:00Z") ?? Date()) ?? 0) / 86400); let position = Int(elapsed) % cycle + 1
    activePlan = ["planId": active["planId"] ?? .null, "revisionId": active["revisionId"] ?? .null, "phaseId": .null, "cyclePosition": .number(Double(position))]
  }
  return .object(["stateVersion": .string("0.1.0"), "subjectId": root["subjectId"] ?? .null, "asOf": .string(asOf), "historyWindow": .object(["type": .string("last_28_days"), "start": .string(lowerDate), "end": .string(asOfDate)]), "activePlan": .object(activePlan), "exerciseState": .object(exerciseState), "familyState": .object([:]), "muscleState": .object([:]), "adherenceState": .object([:]), "sessionState": .array([]), "provenance": .object(["stateVersion": .string("0.1.0"), "asOf": .string(asOf), "historyWindow": .object(["type": .string("last_28_days"), "start": .string(lowerDate), "end": .string(asOfDate)])])])
}

public struct IntentResolver: Sendable {
  public init() {}
  public func resolve(
    _ x: WorkoutIntent, database: FEDatabase? = nil, profile supplied: JSONValue? = nil, target explicitTarget: JSONValue? = nil, relationships: ExerciseRelationships? = nil, history: JSONValue? = nil, asOf: String? = nil
  ) -> IntentResolutionResult {
    let errors = IntentValidator.validate(x, database: database, relationships: relationships)
    if !errors.isEmpty {
      if errors == ["GOAL_POLICY_MISMATCH"] {
        let policyGoal = x.requestedGoalPolicy == "general-strength-v1" ? "strength" : "hypertrophy"
        return IntentResolutionResult(status: "invalid", conflicts: [IntentConflict(code: "GOAL_POLICY_MISMATCH", goal: x.goal, requestedGoalPolicy: x.requestedGoalPolicy, policyGoal: policyGoal)], provenance: ["intentSchemaVersion": s(x.schemaVersion)])
      }
      return IntentResolutionResult(
        status: "invalid",
        conflicts: errors.map {
          IntentConflict(code: $0 == "GOAL_POLICY_MISMATCH" ? $0 : "INVALID_INTENT", detail: $0)
        }, provenance: ["intentSchemaVersion": s(x.schemaVersion)])
    }
    let q = x.schedule
    var missing: [MissingInformation] = []
    if x.goal == nil {
      missing += [.init(field: "goal", reason: "required_for_goal_policy_resolution")]
    }
    if q?.cycleLengthDays == nil {
      missing += [
        .init(field: "schedule.cycleLengthDays", reason: "required_for_schedule_resolution")
      ]
    }
    if q?.sessionsPerCycle == nil {
      missing += [
        .init(field: "schedule.sessionsPerCycle", reason: "required_for_schedule_resolution")
      ]
    }
    let suppliedEquipment: [String] = o(supplied)["equipment"]?.arrayValues.compactMap { $0.stringValue } ?? []
    if x.environment == nil && suppliedEquipment.isEmpty {
      missing += [
        .init(field: "environmentOrEquipment", reason: "required_for_equipment_resolution")
      ]
    }
    if !missing.isEmpty {
      return IntentResolutionResult(status: "needs_clarification", missingInformation: missing, provenance: ["intentSchemaVersion": s(x.schemaVersion)])
    }
    if x.environment == "home_gym" && suppliedEquipment.isEmpty && (x.equipmentOverrides?.addEquipment ?? []).isEmpty { return IntentResolutionResult(status: "needs_clarification", missingInformation: [.init(field: "equipmentOverrides.addEquipment", reason: "home_gym_has_no_v1_preset")], provenance: ["intentSchemaVersion": s(x.schemaVersion)]) }
    if x.environment == "custom" && suppliedEquipment.isEmpty && (x.equipmentOverrides?.addEquipment ?? []).isEmpty { return IntentResolutionResult(status: "needs_clarification", missingInformation: [.init(field: "equipmentOverrides.addEquipment", reason: "required_for_custom_environment")], provenance: ["intentSchemaVersion": s(x.schemaVersion)]) }
    let goal = x.goal!
    let gid =
      x.requestedGoalPolicy
      ?? (goal == "hypertrophy"
        ? "general-hypertrophy-v1" : goal == "strength" ? "general-strength-v1" : nil)
    guard let gid else {
      return IntentResolutionResult(
        status: "needs_clarification",
        missingInformation: [
          .init(field: "requestedGoalPolicy", reason: "no_default_goal_policy_for_goal")
        ], provenance: ["intentSchemaVersion": s(x.schemaVersion)])
    }
    if gid != "general-hypertrophy-v1" && gid != "general-strength-v1" {
      return IntentResolutionResult(
        status: "invalid",
        conflicts: [
          IntentConflict(code: "INVALID_INTENT", detail: "requestedGoalPolicy: unknown goal policy")
        ])
    }
    let isStrength = gid == "general-strength-v1"
    let policyGoal = isStrength ? "strength" : "hypertrophy"
    if goal != policyGoal {
      return IntentResolutionResult(
        status: "invalid",
        conflicts: [
          IntentConflict(
            code: "GOAL_POLICY_MISMATCH", goal: goal, requestedGoalPolicy: gid,
            policyGoal: policyGoal)
        ])
    }
    let policy = o(IntentPolicyCatalog.goals[gid])
    let desc = policy["description"]?.stringValue
    let policyVersion = policy["policyVersion"]?.stringValue ?? "1"
    let env = IntentPolicyCatalog.environments.values.compactMap { value -> (String, [String], String)? in
      let object = o(value)
      guard object["environment"]?.stringValue == x.environment,
        let id = object["policyId"]?.stringValue else { return nil }
      return (id, object["equipment"]?.arrayValues.compactMap(\.stringValue) ?? [], object["policyVersion"]?.stringValue ?? "1")
    }.first
    let input = o(supplied)
    var equipment = Set(
      suppliedEquipment.isEmpty ? (env?.1 ?? []) : suppliedEquipment
    ).union(x.equipmentOverrides?.addEquipment ?? []).subtracting(
      x.equipmentOverrides?.removeEquipment ?? []
    ).sorted()
    if let database { equipment = equipment.filter { database.equipmentVocabulary.contains($0) || $0 == "body only" }.sorted() }
    let resolvedEnvironmentPolicy = suppliedEquipment.isEmpty ? env?.0 : nil
    var p = input
    p["schemaVersion"] = p["schemaVersion"] ?? s("0.1.0")
    p["profileId"] = p["profileId"] ?? s("resolved-profile")
    p["subjectId"] = x.subjectId.map { s($0) } ?? p["subjectId"] ?? .null
    p["goals"] = .array([.object(["type": s(goal)])])
    p["equipment"] = .array(equipment.map(s))
    p["exercisePreferences"] = p["exercisePreferences"] ?? .object([:])
    var av = o(p["availability"])
    av["cycleLengthDays"] = s(q!.cycleLengthDays!)
    av["sessionsPerCycle"] = rangeJSON(q!.sessionsPerCycle!)
    av["preferredDayOffsets"] = .array(
      Set(
        (q?.preferredDayOffsets ?? [])
          + (q?.preferredWeekdays ?? []).compactMap { IntentValidator.weekdays.firstIndex(of: $0) }
      ).sorted().map(s))
    av["excludedDayOffsets"] = .array(
      Set(
        (q?.excludedDayOffsets ?? [])
          + (q?.excludedWeekdays ?? []).compactMap { IntentValidator.weekdays.firstIndex(of: $0) }
      ).sorted().map(s))
    if let r = x.sessionConstraints?.exercisesPerSession {
      av["exercisesPerSession"] = rangeJSON(r)
    }
    p["availability"] = .object(av)
    var constraints = o(p["constraints"])
    let inputConstraints = x.exerciseConstraints
    let excludedExercises = Set((constraints["excludedExerciseIds"]?.arrayValues.compactMap { $0.stringValue } ?? []) + (inputConstraints?.excludedExerciseIds ?? [])).sorted()
    let excludedFamilies = Set((constraints["excludedFamilyIds"]?.arrayValues.compactMap { $0.stringValue } ?? []) + (inputConstraints?.excludedFamilyIds ?? [])).sorted()
    constraints["excludedExerciseIds"] = .array(excludedExercises.map(s)); constraints["excludedFamilyIds"] = .array(excludedFamilies.map(s)); p["constraints"] = .object(constraints)
    let requiredExercises = Set((inputConstraints?.requiredExerciseIds ?? []) + (inputConstraints?.lockedExerciseIds ?? []))
    let requiredFamilies = Set(inputConstraints?.requiredFamilyIds ?? [])
    var constraintConflicts = requiredExercises.intersection(Set(excludedExercises)).sorted().map { IntentConflict(code: "REQUIRED_EXERCISE_EXCLUDED", exerciseId: $0) }
    constraintConflicts += requiredFamilies.intersection(Set(excludedFamilies)).sorted().map { IntentConflict(code: "REQUIRED_FAMILY_EXCLUDED", familyId: $0) }
    if !constraintConflicts.isEmpty { return IntentResolutionResult(status: "invalid", resolvedProfile: .object(p), conflicts: constraintConflicts, provenance: ["intentSchemaVersion": s(x.schemaVersion)]) }
    var preferences = o(p["exercisePreferences"])
    if let inputPreferences = x.preferences { for (key, values) in [("preferredExerciseIds", inputPreferences.preferredExerciseIds), ("avoidedExerciseIds", inputPreferences.avoidedExerciseIds), ("preferredFamilyIds", inputPreferences.preferredFamilyIds), ("avoidedFamilyIds", inputPreferences.avoidedFamilyIds)] where !values.isEmpty { preferences[key] = .array(Set((preferences[key]?.arrayValues.compactMap { $0.stringValue } ?? []) + values).sorted().map(s)) } }
    p["exercisePreferences"] = .object(preferences)
    let gMuscles = policy["muscles"] ?? .object([:])
    let target = merge(
      .object([
        "schemaVersion": s("0.1.0"), "targetId": s("\(gid)-default"),
        "periodDays": s(q!.cycleLengthDays!), "muscles": gMuscles, "notes": s(desc ?? ""),
      ]), explicitTarget)
    let targetErrors = validateTarget(target)
    if !targetErrors.isEmpty { return IntentResolutionResult(status: "invalid", resolvedTarget: target, conflicts: targetErrors.map { IntentConflict(code: "TARGET_OVERRIDE_CONFLICT", detail: $0) }, provenance: ["intentSchemaVersion": s(x.schemaVersion)]) }
    let defaults =
      (x.requestedGoalPolicy == nil ? ["goalPolicy"] : [])
      + (x.requestedPlanningPolicy == nil ? ["planningPolicy"] : [])
      + (resolvedEnvironmentPolicy != nil ? ["environmentPolicy"] : [])
    var historyWarnings: [String] = []
    if x.useHistory == true && history == nil { historyWarnings.append("useHistory was requested but no history was provided") }
    if x.useHistory == true && history != nil && asOf == nil { historyWarnings.append("useHistory was requested but as_of is required to derive TrainingState") }
    let reps = policy["reps"] ?? .object([:])
    var generationOptions: [String: JSONValue] = [
      "continuity": s(x.continuity ?? "neutral"), "repDefaults": reps,
      "effortDefaults": policy["effort"] ?? .object([:]), "requiredFamilyIds": .array((x.exerciseConstraints?.requiredFamilyIds ?? []).sorted().map(s)),
    ]
    if x.useHistory == true, let history, let asOf { generationOptions["trainingState"] = deriveTrainingState(history, asOf: asOf) }
    return IntentResolutionResult(
      status: defaults.isEmpty ? "resolved" : "resolved_with_defaults", resolvedProfile: .object(p),
      resolvedTarget: target, planningPolicy: x.requestedPlanningPolicy ?? "full-body-general-v1",
      goalPolicy: GoalPolicyReference(policyId: gid, policyVersion: policyVersion, description: desc), environmentPolicy: resolvedEnvironmentPolicy,
      generationOptions: .object(generationOptions), missingInformation: [], warnings: historyWarnings, defaultsApplied: defaults,
      explicitOverrides: ExplicitOverrides(
        goalPolicy: x.requestedGoalPolicy != nil, planningPolicy: x.requestedPlanningPolicy != nil,
        target: explicitTarget != nil, trainingProfile: supplied != nil,
        equipmentAdded: x.equipmentOverrides?.addEquipment ?? [],
        equipmentRemoved: x.equipmentOverrides?.removeEquipment ?? []),
      provenance: [
        "intentSchemaVersion": s(x.schemaVersion),
        "goalPolicy": .object(["policyId": s(gid), "policyVersion": s(policyVersion)]),
        "environmentPolicy": resolvedEnvironmentPolicy.map { .object(["policyId": s($0), "policyVersion": s(env?.2 ?? "1")]) } ?? .null,
        "dbSchemaVersion": o(database.map { .object($0.metadata) })["schemaVersion"] ?? .null,
        "dbConverterVersion": o(database.map { .object($0.metadata) })["converterVersion"] ?? .null,
        "relationshipSchemaVersion": relationships.map { s($0.schemaVersion) } ?? .null,
      ])
  }
}
public func validateWorkoutIntent(_ x: WorkoutIntent, database: FEDatabase? = nil, relationships: ExerciseRelationships? = nil) -> [String] { IntentValidator.validate(x, database: database, relationships: relationships) }
public func resolveIntent(_ x: WorkoutIntent, database: FEDatabase? = nil, profile: JSONValue? = nil, target: JSONValue? = nil, relationships: ExerciseRelationships? = nil, history: JSONValue? = nil, asOf: String? = nil)
  -> IntentResolutionResult
{ IntentResolver().resolve(x, database: database, profile: profile, target: target, relationships: relationships, history: history, asOf: asOf) }
public func generatePlanFromIntent(_ x: WorkoutIntent, database: FEDatabase, profile: JSONValue? = nil, target: JSONValue? = nil, relationships: ExerciseRelationships? = nil, history: JSONValue? = nil, asOf: String? = nil) -> JSONValue {
  let resolution = resolveIntent(x, database: database, profile: profile, target: target, relationships: relationships, history: history, asOf: asOf)
  let resolutionJSON = (try? JSONEncoder().encode(resolution)).flatMap { try? JSONDecoder().decode(JSONValue.self, from: $0) } ?? .null
  guard ["resolved", "resolved_with_defaults"].contains(resolution.status), let p = resolution.resolvedProfile?.objectValue, let availability = p["availability"]?.objectValue else { return .object(["resolution": resolutionJSON, "generation": .null]) }
  let range = availability["sessionsPerCycle"]?.objectValue ?? [:]; let count = Int(range["target"]?.numberValue ?? range["min"]?.numberValue ?? 1)
  let exerciseCount = Int(availability["exercisesPerSession"]?.objectValue?["target"]?.numberValue ?? 3)
  let constraints = x.exerciseConstraints
  let excluded = Set(constraints?.excludedExerciseIds ?? [])
  let required = (constraints?.requiredExerciseIds ?? []) + (constraints?.lockedExerciseIds ?? [])
  let ids = Array((required + database.exerciseIDs.sorted().filter { !excluded.contains($0) && !required.contains($0) }).prefix(max(1, exerciseCount)))
  let preferred = (resolution.resolvedProfile?.objectValue?["availability"]?.objectValue?["preferredDayOffsets"]?.arrayValues.compactMap { $0.numberValue.map(Int.init) } ?? [])
  let excludedDays = Set(resolution.resolvedProfile?.objectValue?["availability"]?.objectValue?["excludedDayOffsets"]?.arrayValues.compactMap { $0.numberValue.map(Int.init) } ?? [])
  let cycle = Int(availability["cycleLengthDays"]?.numberValue ?? 7)
  let offsets = (preferred + Array(0..<cycle)).filter { !excludedDays.contains($0) }.reduce(into: [Int]()) { if !$0.contains($1) { $0.append($1) } }.prefix(max(1, count))
  let reps = resolution.generationOptions.objectValue?["repDefaults"] ?? .object([:])
  let sessions: [JSONValue] = offsets.enumerated().map { index, offset in
    let exercises: [JSONValue] = ids.enumerated().map { i, id in
      .object(["prescriptionId": .string("intent-rx-\(index + 1)-\(i + 1)"), "exerciseId": .string(id), "order": .number(Double(i + 1)), "sets": .number(1), "reps": reps])
    }
    return .object(["planSessionId": .string("intent-session-\(index + 1)"), "dayOffset": .number(Double(offset)), "exercises": .array(exercises)])
  }
  return .object(["resolution": resolutionJSON, "generation": .object(["status": .string("generated"), "schemaVersion": .string("0.2.0"), "sessions": .array(sessions)])])
}
public func mergeTarget(_ base: JSONValue, _ explicit: JSONValue?) -> JSONValue {
  merge(base, explicit)
}
public func validateTarget(_ target: JSONValue) -> [String] {
  guard case .object(let root) = target else { return ["<root>: must be an object"] }
  func n(_ v: JSONValue?, _ k: String) -> Double? { o(v)[k]?.numberValue }
  func c(_ v: JSONValue?, _ p: String, _ k: [String]) -> [String] {
    let a = n(v, k[0])
    let b = n(v, k[1])
    let d = n(v, k[2])
    return (a != nil && d != nil && a! > d! ? ["\(p): min must not exceed max"] : [])
      + (a != nil && b != nil && b! < a! ? ["\(p): target must not be below min"] : [])
      + (d != nil && b != nil && b! > d! ? ["\(p): target must not exceed max"] : [])
  }
  var e: [String] = []
  for (sec, k) in [
    ("muscles", ["min", "target", "max"]),
    ("movementPatterns", ["minimumSets", "targetSets", "maximumSets"]),
    ("families", ["minimumSets", "targetSets", "maximumSets"]),
  ] { for (name, v) in o(root[sec]) { e += c(v, "\(sec).\(name)", k) } }
  for (name, v) in o(o(root["frequency"])["muscles"]) {
    e += c(v, "frequency.muscles.\(name)", ["min", "target", "max"])
  }
  return Array(Set(e)).sorted()
}
extension WorkoutIntent {
  public func validate() throws {
    let e = validateWorkoutIntent(self)
    if !e.isEmpty { throw FEDBError.invalidDocument(e.joined(separator: "; ")) }
  }
}
