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

public func deriveTrainingState(_ history: JSONValue, asOf: String, window: TrainingHistoryWindow = .last28Days, relationships: ExerciseRelationships? = nil, database: FEDatabase? = nil) -> JSONValue {
  let root = history.objectValue ?? [:]
  let plans = (root["plans"]?.arrayValues ?? []).compactMap { $0.objectValue }
  let activations = (root["planActivations"]?.arrayValues ?? []).compactMap { $0.objectValue }
  let parsedAsOf = parseOffsetAwareTimestamp(asOf)
  let asOfInstant = parsedAsOf?.date
  let activationCandidates = activations.compactMap { activation -> (plan: [String: JSONValue], activation: [String: JSONValue], date: Date)? in
    guard let from = activation["effectiveFrom"]?.stringValue,
      let fromDate = parseOffsetAwareTimestamp(from)?.date, let asOfInstant,
      fromDate <= asOfInstant,
      activation["effectiveTo"]?.stringValue.map({ parseOffsetAwareTimestamp($0).map { asOfInstant < $0.date } ?? false }) ?? true,
      let plan = plans.first(where: { $0["planId"] == activation["planId"] && $0["revisionId"] == activation["revisionId"] })
    else { return nil }
    return (plan: plan, activation: activation, date: fromDate)
  }
  let activePair: (plan: [String: JSONValue], activation: [String: JSONValue], date: Date)? = {
    guard activationCandidates.count <= 1 else { return nil }
    if let candidate = activationCandidates.first { return candidate }
    let referenced = (root["workouts"]?.arrayValues ?? []).compactMap { raw -> (plan: [String: JSONValue], activation: [String: JSONValue], date: Date)? in
      guard let workout = raw.objectValue, let stamp = workout["startTime"]?.stringValue,
            let date = parseOffsetAwareTimestamp(stamp)?.date, let reference = workout["planReference"]?.objectValue,
            let planId = reference["planId"]?.stringValue,
            let plan = plans.first(where: { $0["planId"]?.stringValue == planId && (reference["revisionId"]?.stringValue == nil || $0["revisionId"]?.stringValue == reference["revisionId"]?.stringValue) })
      else { return nil }
      return (plan: plan, activation: [:], date: date)
    }
    return referenced.max { $0.date < $1.date }
  }()
  let active = activePair?.plan
  guard let asOfInstant else { return .object(["stateVersion": .string("0.1.0"), "subjectId": root["subjectId"] ?? .null, "asOf": .string(asOf), "historyWindow": .null, "activePlan": .object([:]), "exerciseState": .object([:]), "familyState": .object([:]), "muscleState": .object([:]), "adherenceState": .object([:]), "sessionState": .array([]), "provenance": .object(["stateVersion": .string("0.1.0"), "asOf": .string(asOf), "timestampError": .string("asOf must be an offset-aware ISO-8601 timestamp")])]) }
  var calendar = Calendar(identifier: .gregorian); calendar.timeZone = TimeZone(secondsFromGMT: parsedAsOf?.offsetSeconds ?? 0)!
  let asOfDate = calendar.startOfDay(for: asOfInstant)
  func date(_ value: String) -> Date? { ISO8601DateFormatter().date(from: value + "T00:00:00Z") }
  var windowStart = calendar.date(byAdding: .day, value: -27, to: asOfDate)!
  var windowEnd = asOfDate
  var windowType = "last_28_days"
  if case .last7Days = window {
    windowStart = calendar.date(byAdding: .day, value: -6, to: asOfDate)!; windowType = "last_7_days"
  } else if case .custom(let start, let end) = window {
    if let parsedStart = date(String(start.prefix(10))), let parsedEnd = date(String(end.prefix(10))) { windowStart = parsedStart; windowEnd = min(parsedEnd, asOfDate); windowType = "custom_date_range" }
  } else if case .currentPlanCycle = window, let activePair {
    let cycle = max(1, Int(activePair.plan["cycle"]?.objectValue?["lengthDays"]?.numberValue ?? 7))
    let anchor = calendar.startOfDay(for: activePair.date)
    let elapsed = max(0, calendar.dateComponents([.day], from: anchor, to: asOfDate).day ?? 0)
    windowStart = calendar.date(byAdding: .day, value: (elapsed / cycle) * cycle, to: anchor)!
    windowEnd = calendar.date(byAdding: .day, value: cycle - 1, to: windowStart)!
    windowType = "current_plan_cycle"
  } else if case .currentPhase = window, let activePair {
    let anchor = calendar.startOfDay(for: activePair.date)
    var cursor = anchor
    var found = false
    for phase in activePair.plan["phases"]?.arrayValues ?? [] {
      let p = phase.objectValue ?? [:]
      let cycle = max(1, Int((p["cycle"]?.objectValue? ["lengthDays"] ?? activePair.plan["cycle"]?.objectValue?["lengthDays"])?.numberValue ?? 7))
      let length = cycle * max(1, Int(p["durationCycles"]?.numberValue ?? 1))
      let phaseEnd = calendar.date(byAdding: .day, value: length - 1, to: cursor)!
      if cursor <= asOfDate && asOfDate <= phaseEnd { windowStart = cursor; windowEnd = phaseEnd; found = true; break }
      cursor = calendar.date(byAdding: .day, value: length, to: cursor)!
    }
    if found { windowType = "current_phase" }
  }
  windowEnd = min(windowEnd, asOfDate)
  if windowStart > windowEnd { windowStart = windowEnd }
  let dateFormatter = ISO8601DateFormatter(); dateFormatter.timeZone = TimeZone(secondsFromGMT: 0)
  dateFormatter.formatOptions = [.withFullDate]
  let lowerDate = dateFormatter.string(from: windowStart), endDate = dateFormatter.string(from: windowEnd)
  let workouts = (root["workouts"]?.arrayValues ?? []).compactMap { $0.objectValue }.filter {
    let stamp = $0["startTime"]?.stringValue ?? ""
    guard let instant = parseOffsetAwareTimestamp(stamp)?.date else { return false }
    return instant >= windowStart && instant <= asOfInstant && instant <= calendar.date(byAdding: .day, value: 1, to: windowEnd)!.addingTimeInterval(-0.001)
  }
  let countedSetTypes: Set<String> = ["working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"]
  func completedSets(_ exercise: [String: JSONValue]) -> [[String: JSONValue]] {
    (exercise["sets"]?.arrayValues ?? []).compactMap { raw in
      guard let set = raw.objectValue, set["completed"] == .bool(true) else { return nil }
      if let type = set["setType"]?.stringValue, !countedSetTypes.contains(type) { return nil }
      return set
    }
  }
  var exids = Set<String>()
  if let active {
    for session in active["sessions"]?.arrayValues ?? [] {
      for exercise in session.objectValue?["exercises"]?.arrayValues ?? [] {
        if let id = exercise.objectValue?["exerciseId"]?.stringValue { exids.insert(id) }
      }
    }
  }
  for workout in workouts {
    for exercise in workout["exercises"]?.arrayValues ?? [] {
      if let id = exercise.objectValue?["exerciseId"]?.stringValue { exids.insert(id) }
    }
  }
  var exerciseState: [String: JSONValue] = [:]
  for id in exids.sorted() {
    let observations = workouts.flatMap { workout -> [([String: JSONValue], [String: JSONValue])] in
      (workout["exercises"]?.arrayValues ?? []).compactMap { raw in
        guard let exercise = raw.objectValue, exercise["exerciseId"]?.stringValue == id else { return nil }
        return (workout, exercise)
      }
    }.sorted {
      let left = parseOffsetAwareTimestamp($0.0["startTime"]?.stringValue ?? "")?.date ?? .distantPast
      let right = parseOffsetAwareTimestamp($1.0["startTime"]?.stringValue ?? "")?.date ?? .distantPast
      if left != right { return left < right }
      return ($0.0["sessionId"]?.stringValue ?? "") < ($1.0["sessionId"]?.stringValue ?? "")
    }
    let prescribed = active?["sessions"]?.arrayValues.compactMap { $0.objectValue }.flatMap { $0["exercises"]?.arrayValues.compactMap { $0.objectValue } ?? [] }.filter { $0["exerciseId"]?.stringValue == id } ?? []
    let last = observations.last
    let actual = last.map { completedSets($0.1) } ?? []
    let performances: [JSONValue] = observations.map { pair in
      let workout = pair.0, exercise = pair.1
      let sets: [JSONValue] = completedSets(exercise).map { JSONValue.object($0) }
      return JSONValue.object(["sessionId": workout["sessionId"] ?? .null, "timestamp": workout["startTime"] ?? .null, "exerciseId": exercise["exerciseId"] ?? .null, "exercisePrescriptionId": exercise["exercisePrescriptionId"] ?? .null, "sets": .array(sets)])
    }
    let latest = performances.last
    let recentSets = observations.flatMap { completedSets($0.1) }
    let recentReps = recentSets.compactMap { $0["reps"]?.numberValue }.map(JSONValue.number)
    let recentLoads = recentSets.compactMap { $0["load"] }
    let recentRPE = recentSets.compactMap { $0["rpe"]?.numberValue }.map(JSONValue.number)
    let recentRIR = recentSets.compactMap { $0["rir"]?.numberValue }.map(JSONValue.number)
    let recentSetTypes = recentSets.compactMap { $0["setType"] }
    let values: [String: JSONValue] = [
      "exerciseId": .string(id),
      "lastPerformedAt": last?.0["startTime"] ?? .null,
      "lastPrescription": prescribed.first.map(JSONValue.object) ?? .null,
      "lastActual": last == nil ? .null : .object(["exerciseId": .string(id), "sets": .array(actual.map(JSONValue.object))]),
      "latestPerformance": latest ?? .null,
      "recentPerformances": .array(performances),
      "recentSessionCount": .number(Double(observations.count)),
      "recentCompletedSetCount": .number(Double(recentSets.count)),
      "recentReps": .array(recentReps), "recentLoads": .array(recentLoads),
      "recentRPE": .array(recentRPE), "recentRIR": .array(recentRIR),
      "recentSetTypes": .array(recentSetTypes),
      "substitutionCount": .number(Double(observations.filter { $0.1["substitution"] != nil }.count)),
      "unplannedCount": .number(Double(observations.filter { $0.1["exercisePrescriptionId"] == nil }.count)),
      "prescriptionAdherence": .null,
      "prescriptionAdherenceByPrescriptionId": .object([:])
    ]
    exerciseState[id] = .object(values)
  }
  var activePlan: [String: JSONValue] = [:]
  if let active, let fromDate = activePair?.date {
    let cycle = Int(active["cycle"]?.objectValue?["lengthDays"]?.numberValue ?? 7); let elapsed = max(0, calendar.dateComponents([.day], from: calendar.startOfDay(for: fromDate), to: asOfDate).day ?? 0); let position = elapsed % cycle + 1
    activePlan = ["planId": active["planId"] ?? .null, "revisionId": active["revisionId"] ?? .null, "phaseId": .null, "cyclePosition": .number(Double(position))]
  }
  func scalar(_ value: JSONValue?) -> Double? { value?.numberValue }
  func adherence(_ planned: Double?, _ actual: Double) -> JSONValue {
    let p = planned ?? 0
    return .object(["planned": planned.map(JSONValue.number) ?? .null, "actual": .number(actual), "delta": .number(actual - p), "fraction": p == 0 ? .null : .number(actual / p), "comparable": planned == nil ? .bool(false) : .bool(true), "comparedSets": .number(planned == nil ? 0 : 1)])
  }
  func metric(_ planned: [Double], _ actual: [Double]) -> JSONValue {
    guard !planned.isEmpty, planned.count == actual.count else { return .null }
    let p = planned.reduce(0, +), a = actual.reduce(0, +)
    return .object(["planned": .number(p), "actual": .number(a), "delta": .number(a - p), "fraction": p == 0 ? .null : .number(a / p), "comparable": .bool(true), "comparedSets": .number(Double(planned.count))])
  }
  func quantityValue(_ value: JSONValue?) -> Double? { value?.objectValue?["value"]?.numberValue ?? value?.objectValue?["target"]?.numberValue }
  var sessionRows: [JSONValue] = [], exerciseRows: [JSONValue] = [], substitutionHistory: [String: JSONValue] = [:]
  var skippedCounts: [String: Double] = [:], substitutionCounts: [String: Double] = [:]
  let activeSessions = active?["sessions"]?.arrayValues.compactMap { $0.objectValue } ?? []
  for workout in workouts {
    guard let reference = workout["planReference"]?.objectValue,
          let sessionId = reference["planSessionId"]?.stringValue,
          let session = activeSessions.first(where: { $0["planSessionId"]?.stringValue == sessionId }) else { continue }
    let planned = session["exercises"]?.arrayValues.compactMap { $0.objectValue } ?? []
    let actual = workout["exercises"]?.arrayValues.compactMap { $0.objectValue } ?? []
    var matched = 0, substitutions = 0, actualSets = 0, missing = 0
    for rx in planned {
      let pid = rx["prescriptionId"]?.stringValue ?? ""
      let observation = actual.first { $0["exercisePrescriptionId"]?.stringValue == pid } ?? (actual.contains { $0["exercisePrescriptionId"] != nil || $0["substitution"] != nil } ? nil : actual.first { $0["exerciseId"]?.stringValue == rx["exerciseId"]?.stringValue })
      let sets = observation.map(completedSets) ?? []
      let isSubstitution = observation?["substitution"] != nil
      let status = observation == nil ? "missing_prescription" : (isSubstitution ? "substitution" : "matched")
      let plannedSets = scalar(rx["sets"])
      let actualCount = Double(sets.count); actualSets += Int(actualCount)
      if status == "missing_prescription" { missing += 1; skippedCounts[pid, default: 0] += 1 } else { matched += 1 }
      if isSubstitution {
        substitutions += 1; substitutionCounts[pid, default: 0] += 1
        let replacement = observation?["exerciseId"]?.stringValue ?? ""
        let existing = substitutionHistory[pid]?.objectValue ?? [:]
        let count = (existing["count"]?.numberValue ?? 0) + 1
        substitutionHistory[pid] = .object(["count": .number(count), "sessionIds": .array((existing["sessionIds"]?.arrayValues ?? []) + [workout["sessionId"] ?? .null]), "timestamps": .array((existing["timestamps"]?.arrayValues ?? []) + [workout["startTime"] ?? .null]), "replacementExerciseId": .string(replacement)])
      }
      let repsAdherence = metric(sets.compactMap { _ in scalar(rx["reps"]) }, sets.compactMap { $0["reps"]?.numberValue })
      let loadAdherence = metric(sets.compactMap { _ in quantityValue(rx["load"]) }, sets.compactMap { quantityValue($0["load"]) })
      let effort = rx["effort"]?.objectValue ?? [:]
      let rpeAdherence = metric(sets.compactMap { _ in scalar(effort["rpe"]) }, sets.compactMap { $0["rpe"]?.numberValue })
      let rirAdherence = metric(sets.compactMap { _ in scalar(effort["rir"]) }, sets.compactMap { $0["rir"]?.numberValue })
      let row: [String: JSONValue] = ["subjectId": root["subjectId"] ?? .null, "period": .string(lowerDate), "sessionId": workout["sessionId"] ?? .null, "prescriptionId": .string(pid), "plannedExerciseId": rx["exerciseId"] ?? .null, "actualExerciseId": observation?["exerciseId"] ?? .null, "match_status": .string(status), "missingness": observation == nil ? .string("not_recorded") : .null, "planned_sets_min": plannedSets.map(JSONValue.number) ?? .null, "planned_sets_target": plannedSets.map(JSONValue.number) ?? .null, "planned_sets_max": plannedSets.map(JSONValue.number) ?? .null, "actual_sets": .number(actualCount), "set_adherence": adherence(plannedSets, actualCount), "reps_adherence": .null, "load_adherence": .null, "rpe_adherence": .null, "rir_adherence": .null, "substitution_reason": observation?["substitution"]?.objectValue?["reason"] ?? .null]
      var enriched = row
      enriched["reps_adherence"] = repsAdherence; enriched["load_adherence"] = loadAdherence; enriched["rpe_adherence"] = rpeAdherence; enriched["rir_adherence"] = rirAdherence
      exerciseRows.append(.object(enriched))
    }
    let unplanned = actual.filter { item in !planned.contains { $0["prescriptionId"]?.stringValue == item["exercisePrescriptionId"]?.stringValue } }
    for item in unplanned {
      let count = Double(completedSets(item).count); actualSets += Int(count)
      let unable = item["exercisePrescriptionId"]?.stringValue != nil || item["substitution"] != nil
      let status = unable ? "unable_to_match" : "unplanned_addition"
      let missingness = item["exerciseId"]?.stringValue == nil ? "unknown" : (unable ? "unable_to_match" : "not_prescribed")
      exerciseRows.append(.object(["subjectId": root["subjectId"] ?? .null, "period": .string(lowerDate), "sessionId": workout["sessionId"] ?? .null, "prescriptionId": item["exercisePrescriptionId"] ?? .null, "plannedExerciseId": .null, "actualExerciseId": item["exerciseId"] ?? .null, "match_status": .string(status), "missingness": .string(missingness), "planned_sets_min": .null, "planned_sets_target": .null, "planned_sets_max": .null, "actual_sets": .number(count), "set_adherence": .null, "reps_adherence": .null, "load_adherence": .null, "rpe_adherence": .null, "rir_adherence": .null, "substitution_reason": .null]))
    }
    sessionRows.append(.object(["subject_id": root["subjectId"] ?? .null, "period_type": .string("custom_date_range"), "period_start": .string(lowerDate), "period_end": .string(endDate), "scheduled_date": .null, "session_id": workout["sessionId"] ?? .null, "timestamp": workout["startTime"] ?? .null, "plan_id": reference["planId"] ?? .null, "revision_id": reference["revisionId"] ?? .null, "plan_session_id": .string(sessionId), "session_status": .string(missing == planned.count ? "missed_planned_session" : "matched"), "planned_exercises": .number(Double(planned.count)), "matched_exercises": .number(Double(matched)), "substitutions": .number(Double(substitutions)), "unplanned_exercises": .number(Double(unplanned.count)), "planned_sets": .number(planned.compactMap { scalar($0["sets"]) }.reduce(0, +)), "actual_counted_sets": .number(Double(actualSets)), "missing_prescriptions": .number(Double(missing)), "missed_sets": .number(0), "unplanned_sets": .number(Double(unplanned.reduce(0) { $0 + completedSets($1).count })), "session_adherence": .number(missing == 0 ? 1 : 0)]))
  }
  let skipped = skippedCounts.mapValues { JSONValue.number($0) }, substitutions = substitutionCounts.mapValues { JSONValue.number($0) }
  let adherenceState: JSONValue = .object(["sessionAdherence": .array(sessionRows), "exercisePrescriptionAdherence": .array(exerciseRows), "substitutionAdjustedCompletion": .number(Double(exerciseRows.filter { ["matched", "substitution"].contains($0.objectValue?["match_status"]?.stringValue) }.count)), "missedScheduledOccurrences": .array(sessionRows.filter { $0.objectValue?["session_status"] == .string("missed_planned_session") }), "repeatedSkippedExercises": .array(skipped.keys.sorted().map(JSONValue.string)), "repeatedSubstitutions": .array(substitutions.keys.sorted().map(JSONValue.string)), "skippedPrescriptionCounts": .object(skipped), "substitutionCountsByPrescription": .object(substitutions), "substitutionHistoryByPrescription": .object(substitutionHistory), "unplannedExercises": .array(exerciseRows.filter { $0.objectValue?["match_status"] == .string("unplanned_addition") }), "unplannedSets": .number(Double(exerciseRows.filter { $0.objectValue?["match_status"] == .string("unplanned_addition") }.reduce(0) { $0 + Int($1.objectValue?["actual_sets"]?.numberValue ?? 0) }))])
  var muscleState: [String: JSONValue] = [:]
  var muscleExposureSessions: [String: Set<String>] = [:]
  for workout in workouts {
    let sessionId = workout["sessionId"]?.stringValue ?? ""
    for raw in workout["exercises"]?.arrayValues ?? [] {
      guard let exercise = raw.objectValue, let id = exercise["exerciseId"]?.stringValue else { continue }
      let count = Double(completedSets(exercise).count); guard count > 0 else { continue }
      guard let database, let annotation = try? database.getExercise(id).annotation else { continue }
      func add(_ muscle: String, direct: Double, indirect: Double, stabilizer: Double) {
        var row = muscleState[muscle]?.objectValue ?? ["muscleId": .string(muscle), "directSets": .number(0), "indirectSets": .number(0), "stabilizerSets": .number(0), "effectiveSets": .number(0), "exposures": .number(0), "mappedFraction": .number(1)]
        row["directSets"] = .number((row["directSets"]?.numberValue ?? 0) + direct)
        row["indirectSets"] = .number((row["indirectSets"]?.numberValue ?? 0) + indirect)
        row["stabilizerSets"] = .number((row["stabilizerSets"]?.numberValue ?? 0) + stabilizer)
        row["effectiveSets"] = .number((row["effectiveSets"]?.numberValue ?? 0) + direct * database.setCredits.direct + indirect * database.setCredits.indirect + stabilizer * database.setCredits.stabilizer)
        muscleState[muscle] = .object(row); muscleExposureSessions[muscle, default: []].insert(sessionId)
      }
      for muscle in annotation.direct { add(muscle, direct: count, indirect: 0, stabilizer: 0) }
      for muscle in annotation.indirect { add(muscle, direct: 0, indirect: count, stabilizer: 0) }
      for muscle in annotation.stabilizers { add(muscle, direct: 0, indirect: 0, stabilizer: count) }
    }
  }
  for (muscle, sessions) in muscleExposureSessions { if var row = muscleState[muscle]?.objectValue { row["exposures"] = .number(Double(sessions.count)); muscleState[muscle] = .object(row) } }
  if let target = (root["targets"]?.arrayValues ?? []).first?.objectValue?["muscles"]?.objectValue {
    for (muscle, targetValue) in target { guard var row = muscleState[muscle]?.objectValue else { continue }; let actual = row["effectiveSets"]?.numberValue ?? 0; let range = targetValue.objectValue ?? [:]; let minimum = range["min"]?.numberValue ?? range["minimumSets"]?.numberValue; let desired = range["target"]?.numberValue ?? range["targetSets"]?.numberValue; let maximum = range["max"]?.numberValue ?? range["maximumSets"]?.numberValue; let state = minimum.map { actual < $0 ? "below_minimum" : (maximum.map { actual > $0 } ?? false ? "above_maximum" : (desired.map { actual < $0 } ?? false ? "within_range_below_target" : (desired.map { actual > $0 } ?? false ? "within_range_above_target" : (desired != nil ? "at_target" : "within_range")))) } ?? "not_targeted"; row["targetState"] = .string(state); row["plannedVsActual"] = .object(["planned": desired.map(JSONValue.number) ?? .null, "actual": .number(actual)]); muscleState[muscle] = .object(row) }
  }
  var familyState: [String: JSONValue] = [:]
  if let relationships {
    for id in exerciseState.keys.sorted() {
      guard let family = relationships.family(for: id) else { continue }
      var row = familyState[family.familyId]?.objectValue ?? ["familyId": .string(family.familyId), "recentExerciseIds": .array([]), "explicitSubstitutionCount": .number(0), "variantHistory": .array([])]
      if case .array(let ids) = row["recentExerciseIds"] { row["recentExerciseIds"] = .array((ids + [.string(id)]).sorted { $0.stringValue ?? "" < $1.stringValue ?? "" }) }
      row["explicitSubstitutionCount"] = .number((row["explicitSubstitutionCount"]?.numberValue ?? 0) + (exerciseState[id]?.objectValue?["substitutionCount"]?.numberValue ?? 0))
      familyState[family.familyId] = .object(row)
    }
    for (id, value) in familyState {
      guard case .object(var row) = value, case .array(let ids) = row["recentExerciseIds"] else { continue }
      let mostRecent = ids.compactMap { $0.stringValue }.max { a, b in
        let left = exerciseState[a]?.objectValue?["lastPerformedAt"]?.stringValue ?? ""
        let right = exerciseState[b]?.objectValue?["lastPerformedAt"]?.stringValue ?? ""
        return left < right
      }
      row["mostRecentExerciseId"] = mostRecent.map(JSONValue.string) ?? .null
      familyState[id] = .object(row)
    }
  }
  return .object(["stateVersion": .string("0.1.0"), "subjectId": root["subjectId"] ?? .null, "asOf": .string(asOf), "historyWindow": .object(["type": .string(windowType), "start": .string(lowerDate), "end": .string(endDate)]), "activePlan": .object(activePlan), "exerciseState": .object(exerciseState), "familyState": .object(familyState), "muscleState": .object(muscleState), "adherenceState": adherenceState, "sessionState": .array(sessionRows), "provenance": .object(["stateVersion": .string("0.1.0"), "asOf": .string(asOf), "historyWindow": .object(["type": .string(windowType), "start": .string(lowerDate), "end": .string(endDate), "timezoneOffsetSeconds": .number(Double(parsedAsOf?.offsetSeconds ?? 0))])])])
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
