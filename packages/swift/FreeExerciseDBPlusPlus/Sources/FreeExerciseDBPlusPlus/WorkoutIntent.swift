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
    self.equipmentAdded = equipmentAdded.sorted()
    self.equipmentRemoved = equipmentRemoved.sorted()
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
  public static func validate(_ x: WorkoutIntent) -> [String] {
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
    if x.requestedGoalPolicy == "general-strength-v1" && x.goal == "hypertrophy"
      || x.requestedGoalPolicy == "general-hypertrophy-v1" && x.goal == "strength"
    {
      e += ["GOAL_POLICY_MISMATCH"]
    }
    if let policy = x.requestedPlanningPolicy,
      !["full-body-general-v1", "upper-lower-general-v1"].contains(policy)
    {
      e += ["requestedPlanningPolicy: unknown planning policy"]
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
public struct IntentResolver: Sendable {
  public init() {}
  public func resolve(
    _ x: WorkoutIntent, profile supplied: JSONValue? = nil, target explicitTarget: JSONValue? = nil
  ) -> IntentResolutionResult {
    let errors = IntentValidator.validate(x)
    if !errors.isEmpty {
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
    if x.environment == nil && supplied == nil {
      missing += [
        .init(field: "environmentOrEquipment", reason: "required_for_equipment_resolution")
      ]
    }
    if !missing.isEmpty {
      return IntentResolutionResult(status: "needs_clarification", missingInformation: missing)
    }
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
        ])
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
    let desc =
      isStrength
      ? "Minimal generic strength defaults; exercise-specific strength programming remains out of scope."
      : "General, conservative coverage defaults; not an optimal prescription."
    let envMap: [String: (String, [String])] = [
      "commercial_gym": (
        "commercial-gym-general-v1",
        [
          "bands", "barbell", "body only", "cable", "dumbbell", "e-z curl bar", "exercise ball",
          "kettlebells", "machine", "medicine ball",
        ]
      ), "bodyweight_only": ("bodyweight-only-v1", ["body only"]),
      "minimal_equipment": ("minimal-equipment-general-v1", ["bands", "body only", "dumbbell"]),
    ]
    let env = x.environment.flatMap { envMap[$0] }
    let input = o(supplied)
    let equipment = Set(
      input["equipment"]?.arrayValues.compactMap { $0.stringValue } ?? env?.1 ?? []
    ).union(x.equipmentOverrides?.addEquipment ?? []).subtracting(
      x.equipmentOverrides?.removeEquipment ?? []
    ).sorted()
    var p = input
    p["schemaVersion"] = p["schemaVersion"] ?? s("0.1.0")
    p["profileId"] = p["profileId"] ?? s("resolved-profile")
    p["subjectId"] = x.subjectId.map { s($0) } ?? p["subjectId"] ?? .null
    p["goals"] = .array([.object(["type": s(goal)])])
    p["equipment"] = .array(equipment.map(s))
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
    p["constraints"] =
      p["constraints"]
      ?? .object(["excludedExerciseIds": .array([]), "excludedFamilyIds": .array([])])
    let gMuscles: JSONValue =
      isStrength
      ? .object([
        "chest": .object(["target": s(3)]), "quadriceps": .object(["target": s(3)]),
        "hamstrings": .object(["target": s(2)]),
      ])
      : .object([
        "chest": .object(["target": s(6)]), "lats": .object(["target": s(6)]),
        "quadriceps": .object(["target": s(6)]), "hamstrings": .object(["target": s(4)]),
      ])
    let target = merge(
      .object([
        "schemaVersion": s("0.1.0"), "targetId": s("\(gid)-default"),
        "periodDays": s(q!.cycleLengthDays!), "muscles": gMuscles, "notes": s(desc),
      ]), explicitTarget)
    let defaults =
      (x.requestedGoalPolicy == nil ? ["goalPolicy"] : [])
      + (x.requestedPlanningPolicy == nil ? ["planningPolicy"] : [])
      + (env != nil && supplied == nil ? ["environmentPolicy"] : [])
    let reps: JSONValue =
      isStrength
      ? .object(["min": s(3), "target": s(5), "max": s(6)])
      : .object(["min": s(6), "target": s(8), "max": s(12)])
    return IntentResolutionResult(
      status: defaults.isEmpty ? "resolved" : "resolved_with_defaults", resolvedProfile: .object(p),
      resolvedTarget: target, planningPolicy: x.requestedPlanningPolicy ?? "full-body-general-v1",
      goalPolicy: GoalPolicyReference(policyId: gid, description: desc), environmentPolicy: env?.0,
      generationOptions: .object([
        "continuity": s(x.continuity ?? "neutral"), "repDefaults": reps,
        "effortDefaults": .object(["rir": s(2)]), "requiredFamilyIds": .array([]),
      ]), defaultsApplied: defaults,
      explicitOverrides: ExplicitOverrides(
        goalPolicy: x.requestedGoalPolicy != nil, planningPolicy: x.requestedPlanningPolicy != nil,
        target: explicitTarget != nil, trainingProfile: supplied != nil,
        equipmentAdded: x.equipmentOverrides?.addEquipment ?? [],
        equipmentRemoved: x.equipmentOverrides?.removeEquipment ?? []),
      provenance: [
        "intentSchemaVersion": s(x.schemaVersion),
        "goalPolicy": .object(["policyId": s(gid), "policyVersion": s("1")]),
        "environmentPolicy": env.map { .object(["policyId": s($0.0), "policyVersion": s("1")]) }
          ?? .null,
      ])
  }
}
public func validateWorkoutIntent(_ x: WorkoutIntent) -> [String] { IntentValidator.validate(x) }
public func resolveIntent(_ x: WorkoutIntent, profile: JSONValue? = nil, target: JSONValue? = nil)
  -> IntentResolutionResult
{ IntentResolver().resolve(x, profile: profile, target: target) }
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
