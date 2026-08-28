import Foundation

// MARK: - Stable application result models

/// A goal entry in a `TrainingProfile`.
public struct TrainingGoal: Codable, Sendable, Equatable {
  public let type: String
  public let priority: Int?
  public init(type: String, priority: Int? = nil) { self.type = type; self.priority = priority }
}

/// Closed profile constraint fields defined by the current profile schema.
public struct ProfileConstraints: Codable, Sendable, Equatable {
  public let excludedExerciseIds: [String]
  public let excludedFamilyIds: [String]
  public init(excludedExerciseIds: [String] = [], excludedFamilyIds: [String] = []) {
    self.excludedExerciseIds = excludedExerciseIds; self.excludedFamilyIds = excludedFamilyIds
  }
}

/// Typed summary of a derived muscle-volume row.
public struct MuscleState: Codable, Sendable, Equatable {
  public let actualEffectiveSets: Double?
  public let target: Double?
  public let minimum: Double?
  public let maximum: Double?
  public let state: String?
  public init(actualEffectiveSets: Double? = nil, target: Double? = nil,
              minimum: Double? = nil, maximum: Double? = nil, state: String? = nil) {
    self.actualEffectiveSets = actualEffectiveSets; self.target = target
    self.minimum = minimum; self.maximum = maximum; self.state = state
  }
}

/// Typed summary of a derived exercise-family row.
public struct FamilyState: Codable, Sendable, Equatable {
  public let plannedSets: Double?
  public let target: Double?
  public let minimum: Double?
  public let maximum: Double?
  public let state: String?
  public init(plannedSets: Double? = nil, target: Double? = nil,
              minimum: Double? = nil, maximum: Double? = nil, state: String? = nil) {
    self.plannedSets = plannedSets; self.target = target; self.minimum = minimum
    self.maximum = maximum; self.state = state
  }
}

/// Typed high-level adherence counters from `TrainingState`.
public struct AdherenceState: Codable, Sendable, Equatable {
  public let unplannedSets: Int
  public let substitutionAdjustedCompletion: Double
  public init(unplannedSets: Int = 0, substitutionAdjustedCompletion: Double = 0) {
    self.unplannedSets = unplannedSets; self.substitutionAdjustedCompletion = substitutionAdjustedCompletion
  }
}

public extension TrainingState {
  /// Typed muscle rows; the original `muscleState` map remains available for
  /// schema extensions and v1.11 source compatibility.
  var muscles: [String: MuscleState] { typedRows(muscleState, as: MuscleState.self) }
  /// Typed family rows; the original map remains available for extensions.
  var families: [String: FamilyState] { typedRows(familyState, as: FamilyState.self) }
  /// Typed high-level adherence counters.
  var adherence: AdherenceState {
    let count: Int = if case .number(let value)? = adherenceState["unplannedSets"] { Int(value) } else { 0 }
    let completion: Double = if case .number(let value)? = adherenceState["substitutionAdjustedCompletion"] { value } else { 0 }
    return AdherenceState(unplannedSets: count, substitutionAdjustedCompletion: completion)
  }
}

public extension IntentResolutionResult {
  /// The resolved profile as a typed domain value, when resolution produced one.
  var resolvedTrainingProfile: TrainingProfile? {
    guard let value = resolvedProfile else { return nil }
    return try? decodeApplication(TrainingProfile.self, value: value)
  }

  /// The resolved target as a typed domain value, when resolution produced one.
  var resolvedVolumeTarget: VolumeTarget? {
    guard let value = resolvedTarget else { return nil }
    return try? decodeApplication(VolumeTarget.self, value: value)
  }
}

private func typedRows<T: Decodable>(_ values: [String: JSONValue], as type: T.Type) -> [String: T] {
  values.compactMapValues { value in
    guard let data = try? JSONEncoder().encode(value) else { return nil }
    return try? JSONDecoder().decode(type, from: data)
  }
}

private func decodeApplication<T: Decodable>(_ type: T.Type, value: JSONValue) throws -> T {
  try JSONDecoder().decode(type, from: JSONEncoder().encode(value))
}

/// A machine-readable validation issue. The engine never uses localized text
/// as the primary contract; applications can choose how to present `message`.
public struct IntentValidationIssue: Codable, Sendable, Equatable {
  public let code: String
  public let field: String?
  public let message: String?

  public init(code: String, field: String? = nil, message: String? = nil) {
    self.code = code
    self.field = field
    self.message = message
  }
}

/// The structured result of validating a `WorkoutIntent`.
public struct IntentValidationResult: Codable, Sendable, Equatable {
  public static let validStatus = "valid"
  public static let invalidStatus = "invalid"

  public let status: String
  public let issues: [IntentValidationIssue]

  public init(status: String, issues: [IntentValidationIssue] = []) {
    self.status = status
    self.issues = issues
  }

  public var isValid: Bool { status == Self.validStatus && issues.isEmpty }
}

/// A stable, typed view of a canonical evaluation row. Additional row fields
/// remain owned by the versioned evaluation artifact and are not required for
/// ordinary app decisions.
public struct PlanEvaluationRow: Codable, Sendable, Equatable {
  public let actualEffectiveSets: Double?
  public let plannedSets: Double?
  public let minimum: Double?
  public let target: Double?
  public let maximum: Double?
  public let state: String?

  public init(actualEffectiveSets: Double? = nil, plannedSets: Double? = nil,
              minimum: Double? = nil, target: Double? = nil,
              maximum: Double? = nil, state: String? = nil) {
    self.actualEffectiveSets = actualEffectiveSets
    self.plannedSets = plannedSets
    self.minimum = minimum
    self.target = target
    self.maximum = maximum
    self.state = state
  }
}

/// Summary fields shared by all supported `PlanEvaluation` documents.
public struct PlanEvaluationSummary: Codable, Sendable, Equatable {
  public let hardConstraintViolations: Int
  public let targetGaps: Int
  public let softPreferenceWarnings: Int
  public let satisfiesHardConstraints: Bool
  public let meetsTargetMinimums: Bool
  public let evaluationStatus: String

  public init(hardConstraintViolations: Int = 0, targetGaps: Int = 0,
              softPreferenceWarnings: Int = 0, satisfiesHardConstraints: Bool = true,
              meetsTargetMinimums: Bool = true, evaluationStatus: String = "valid") {
    self.hardConstraintViolations = hardConstraintViolations
    self.targetGaps = targetGaps
    self.softPreferenceWarnings = softPreferenceWarnings
    self.satisfiesHardConstraints = satisfiesHardConstraints
    self.meetsTargetMinimums = meetsTargetMinimums
    self.evaluationStatus = evaluationStatus
  }
}

/// A typed application-facing PLAN evaluation. The underlying canonical
/// document is retained privately so unknown future fields round-trip without
/// forcing app code to manipulate `JSONValue`.
public struct PlanEvaluation: Codable, Sendable, Equatable {
  private let document: JSONValue

  public init(document: JSONValue) { self.document = document }

  public var status: String { summary.evaluationStatus }
  public var summary: PlanEvaluationSummary {
    let value = document.objectValue?["summary"]?.objectValue ?? [:]
    return PlanEvaluationSummary(
      hardConstraintViolations: int(value["hardConstraintViolations"]),
      targetGaps: int(value["targetGaps"]),
      softPreferenceWarnings: int(value["softPreferenceWarnings"]),
      satisfiesHardConstraints: bool(value["satisfiesHardConstraints"]) ?? false,
      meetsTargetMinimums: bool(value["meetsTargetMinimums"]) ?? false,
      evaluationStatus: string(value["evaluationStatus"]) ?? "invalid")
  }
  public var muscleCoverage: [String: PlanEvaluationRow] { rows("muscleCoverage") }
  public var frequency: [String: PlanEvaluationRow] { rows("frequency") }
  public var movementPatterns: [String: PlanEvaluationRow] { rows("movementPatterns") }
  public var warnings: [String] {
    guard case .array(let values)? = document.objectValue?["warnings"] else { return [] }
    return values.compactMap(string)
  }
  public var provenance: [String: JSONValue] { document.objectValue?["provenance"]?.objectValue ?? [:] }

  public func encode(to encoder: Encoder) throws { try document.encode(to: encoder) }
  public init(from decoder: Decoder) throws { document = try JSONValue(from: decoder) }

  private func rows(_ key: String) -> [String: PlanEvaluationRow] {
    guard let values = document.objectValue?[key]?.objectValue else { return [:] }
    return values.reduce(into: [:]) { result, pair in
      let row = pair.value.objectValue ?? [:]
      result[pair.key] = PlanEvaluationRow(
        actualEffectiveSets: number(row["actualEffectiveSets"]),
        plannedSets: number(row["plannedSets"]),
        minimum: number(row["minimum"]) ?? number(row["min"]), target: number(row["target"]),
        maximum: number(row["maximum"]) ?? number(row["max"]), state: string(row["state"]))
    }
  }

  private func number(_ value: JSONValue?) -> Double? { if case .number(let x)? = value { return x }; return nil }
  private func int(_ value: JSONValue?) -> Int { Int(number(value) ?? 0) }
  private func bool(_ value: JSONValue?) -> Bool? { if case .bool(let x)? = value { return x }; return nil }
  private func string(_ value: JSONValue?) -> String? { if case .string(let x)? = value { return x }; return nil }
}

/// A machine-readable generation conflict or unsatisfied target.
public struct PlanIssue: Codable, Sendable, Equatable {
  public let code: String
  public let detail: String?
  public let exerciseId: String?
  public let familyId: String?
  public let sessionId: String?
  public let prescriptionId: String?

  public init(code: String, detail: String? = nil, exerciseId: String? = nil,
              familyId: String? = nil, sessionId: String? = nil,
              prescriptionId: String? = nil) {
    self.code = code; self.detail = detail; self.exerciseId = exerciseId
    self.familyId = familyId; self.sessionId = sessionId; self.prescriptionId = prescriptionId
  }
}

/// A concrete change proposed by adaptive coaching.
public struct PlanChange: Codable, Sendable, Equatable {
  public let type: String
  public let prescriptionId: String?
  public let before: [String: JSONValue]
  public let after: [String: JSONValue]
  public let reasonCodes: [String]
  public let decisionIds: [String]

  public init(type: String, prescriptionId: String? = nil,
              before: [String: JSONValue] = [:], after: [String: JSONValue] = [:],
              reasonCodes: [String] = [], decisionIds: [String] = []) {
    self.type = type; self.prescriptionId = prescriptionId; self.before = before
    self.after = after; self.reasonCodes = reasonCodes; self.decisionIds = decisionIds
  }
}

/// Typed request for the deterministic production generator.
public struct PlanGenerationRequest: Codable, Sendable, Equatable {
  public let profile: TrainingProfile
  public let target: VolumeTarget
  public let policy: String
  public let trainingState: TrainingState?
  public let currentPlan: WorkoutPlan?
  public let requiredExerciseIds: [String]
  public let lockedExerciseIds: [String]
  public let requiredFamilyIds: [String]
  public let additionalExclusions: [String]

  public init(profile: TrainingProfile, target: VolumeTarget,
              policy: String = "full-body-general-v1", trainingState: TrainingState? = nil,
              currentPlan: WorkoutPlan? = nil, requiredExerciseIds: [String] = [],
              lockedExerciseIds: [String] = [], requiredFamilyIds: [String] = [],
              additionalExclusions: [String] = []) {
    self.profile = profile; self.target = target; self.policy = policy
    self.trainingState = trainingState; self.currentPlan = currentPlan
    self.requiredExerciseIds = requiredExerciseIds; self.lockedExerciseIds = lockedExerciseIds
    self.requiredFamilyIds = requiredFamilyIds; self.additionalExclusions = additionalExclusions
  }
}

/// Structured output from deterministic PLAN generation.
public struct GeneratedPlanResult: Codable, Sendable, Equatable {
  public let status: String
  public let plan: WorkoutPlan?
  public let evaluation: PlanEvaluation?
  public let policy: JSONValue?
  public let unsatisfiedConstraints: [PlanIssue]
  public let unsatisfiedTargets: [PlanIssue]
  public let unsatisfiedSoftPreferences: [PlanIssue]
  public let provenance: [String: JSONValue]

  public init(status: String, plan: WorkoutPlan? = nil, evaluation: PlanEvaluation? = nil,
              policy: JSONValue? = nil, unsatisfiedConstraints: [PlanIssue] = [],
              unsatisfiedTargets: [PlanIssue] = [], unsatisfiedSoftPreferences: [PlanIssue] = [],
              provenance: [String: JSONValue] = [:]) {
    self.status = status; self.plan = plan; self.evaluation = evaluation; self.policy = policy
    self.unsatisfiedConstraints = unsatisfiedConstraints; self.unsatisfiedTargets = unsatisfiedTargets
    self.unsatisfiedSoftPreferences = unsatisfiedSoftPreferences; self.provenance = provenance
  }
}

/// The combined result of intent resolution followed by optional PLAN
/// generation. `generation` is nil when the intent needs clarification or is
/// invalid.
public struct IntentPlanResult: Codable, Sendable, Equatable {
  public let resolution: IntentResolutionResult
  public let generation: GeneratedPlanResult?

  public init(resolution: IntentResolutionResult, generation: GeneratedPlanResult? = nil) {
    self.resolution = resolution; self.generation = generation
  }

  /// Compatibility view for v1.11 callers. New application code should use
  /// `resolution` and the typed `generation` properties directly.
  @available(*, deprecated, message: "Use resolution and generation instead of JSONValue.")
  public var objectValue: [String: JSONValue]? { applicationJSON(self)?.objectValue }
}

/// Typed request for history-aware adaptive coaching.
public struct PlanAdaptationRequest: Codable, Sendable, Equatable {
  public let profile: TrainingProfile
  public let target: VolumeTarget
  public let currentPlan: WorkoutPlan
  public let history: TrainingHistory?
  public let trainingState: TrainingState?
  public let asOf: Date?
  public let policy: String
  public let planningPolicy: String?

  public init(profile: TrainingProfile, target: VolumeTarget, currentPlan: WorkoutPlan,
              history: TrainingHistory? = nil, trainingState: TrainingState? = nil,
              asOf: Date? = nil, policy: String = "general-adaptive-v1",
              planningPolicy: String? = nil) {
    self.profile = profile; self.target = target; self.currentPlan = currentPlan
    self.history = history; self.trainingState = trainingState; self.asOf = asOf
    self.policy = policy; self.planningPolicy = planningPolicy
  }
}

/// Structured output from adaptive coaching. The proposed PLAN is advisory;
/// the host application decides whether to activate it.
public struct AdaptivePlanResult: Codable, Sendable, Equatable {
  public let status: String
  public let currentPlan: WorkoutPlan?
  public let proposedPlan: WorkoutPlan?
  public let decisions: [CoachDecision]
  public let currentEvaluation: PlanEvaluation?
  public let proposedEvaluation: PlanEvaluation?
  public let trainingState: TrainingState?
  public let changes: [PlanChange]
  public let unresolvedIssues: [PlanIssue]
  public let provenance: [String: JSONValue]

  public init(status: String, currentPlan: WorkoutPlan? = nil, proposedPlan: WorkoutPlan? = nil,
              decisions: [CoachDecision] = [], currentEvaluation: PlanEvaluation? = nil,
              proposedEvaluation: PlanEvaluation? = nil, trainingState: TrainingState? = nil,
              changes: [PlanChange] = [], unresolvedIssues: [PlanIssue] = [],
              provenance: [String: JSONValue] = [:]) {
    self.status = status; self.currentPlan = currentPlan; self.proposedPlan = proposedPlan
    self.decisions = decisions; self.currentEvaluation = currentEvaluation
    self.proposedEvaluation = proposedEvaluation; self.trainingState = trainingState
    self.changes = changes; self.unresolvedIssues = unresolvedIssues; self.provenance = provenance
  }
}

// MARK: - Canonical conversions

private func applicationJSON<T: Encodable>(_ value: T) -> JSONValue? {
  guard let data = try? JSONEncoder().encode(value) else { return nil }
  return try? JSONDecoder().decode(JSONValue.self, from: data)
}

public extension TrainingProfile {
  /// Convenience initializer for the schema's closed typed goal, preference,
  /// and constraint fields. The legacy JSON-backed initializer remains for
  /// forward-compatible extension data.
  init(schemaVersion: String = "0.1.0", profileId: String, subjectId: String? = nil,
       goals: [TrainingGoal], experience: String? = nil,
       availability: TrainingAvailability? = nil, equipment: [String] = [],
       exercisePreferences: WorkoutPreferences = WorkoutPreferences(),
       constraints: ProfileConstraints = ProfileConstraints()) {
    self.init(schemaVersion: schemaVersion, profileId: profileId, subjectId: subjectId,
      goals: goals.compactMap(applicationJSON), experience: experience, availability: availability,
      equipment: equipment, exercisePreferences: applicationJSON(exercisePreferences)?.objectValue ?? [:],
      constraints: applicationJSON(constraints)?.objectValue ?? [:])
  }

  /// Typed view of the profile's closed goal entries.
  var typedGoals: [TrainingGoal] {
    goals.compactMap { value in
      guard let data = try? JSONEncoder().encode(value) else { return nil }
      return try? JSONDecoder().decode(TrainingGoal.self, from: data)
    }
  }

  /// Typed view of closed exercise preferences.
  var typedExercisePreferences: WorkoutPreferences {
    guard let data = try? JSONEncoder().encode(JSONValue.object(exercisePreferences)) else { return WorkoutPreferences() }
    return (try? JSONDecoder().decode(WorkoutPreferences.self, from: data)) ?? WorkoutPreferences()
  }

  /// Typed view of closed profile constraints.
  var typedConstraints: ProfileConstraints {
    guard let data = try? JSONEncoder().encode(JSONValue.object(constraints)) else { return ProfileConstraints() }
    return (try? JSONDecoder().decode(ProfileConstraints.self, from: data)) ?? ProfileConstraints()
  }
}

private func applicationDate(_ date: Date?) -> String? {
  guard let date else { return nil }
  let formatter = ISO8601DateFormatter()
  formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
  return formatter.string(from: date)
}

private func applicationIssues(_ value: JSONValue?) -> [PlanIssue] {
  guard case .array(let values)? = value else { return [] }
  return values.compactMap { raw in
    let object = raw.objectValue ?? [:]
    guard case .string(let code)? = object["code"] else { return nil }
    func string(_ key: String) -> String? { if case .string(let value)? = object[key] { return value }; return nil }
    return PlanIssue(code: code, detail: string("detail"), exerciseId: string("exerciseId"),
                     familyId: string("familyId"), sessionId: string("sessionId"),
                     prescriptionId: string("prescriptionId"))
  }
}

private func applicationChanges(_ value: JSONValue?) -> [PlanChange] {
  guard case .array(let values)? = value else { return [] }
  return values.compactMap { raw in
    let object = raw.objectValue ?? [:]
    func string(_ key: String) -> String? { if case .string(let value)? = object[key] { return value }; return nil }
    func strings(_ key: String) -> [String] {
      guard case .array(let values)? = object[key] else { return [] }
      return values.compactMap(stringValue)
    }
    func dictionary(_ key: String) -> [String: JSONValue] { object[key]?.objectValue ?? [:] }
    guard let type = string("type") else { return nil }
    return PlanChange(type: type, prescriptionId: string("prescriptionId"),
      before: dictionary("before"), after: dictionary("after"),
      reasonCodes: strings("reasonCodes"), decisionIds: strings("decisionIds"))
  }
}

private func stringValue(_ value: JSONValue) -> String? { if case .string(let value) = value { return value }; return nil }

private func applicationGenerated(_ raw: JSONValue) -> GeneratedPlanResult {
  let object = raw.objectValue ?? [:]
  func string(_ key: String) -> String? { if case .string(let value)? = object[key] { return value }; return nil }
  func typed<T: Decodable>(_ type: T.Type, _ value: JSONValue?) -> T? {
    guard let value, value != .null, let data = try? JSONEncoder().encode(value) else { return nil }
    return try? JSONDecoder().decode(type, from: data)
  }
  return GeneratedPlanResult(status: string("status") ?? "invalid_input",
    plan: typed(WorkoutPlan.self, object["plan"]),
    evaluation: typed(PlanEvaluation.self, object["evaluation"]), policy: object["policy"],
    unsatisfiedConstraints: applicationIssues(object["unsatisfiedConstraints"]),
    unsatisfiedTargets: applicationIssues(object["unsatisfiedTargets"]),
    unsatisfiedSoftPreferences: applicationIssues(object["unsatisfiedSoftPreferences"]),
    provenance: object["provenance"]?.objectValue ?? [:])
}

private func applicationAdaptive(_ raw: JSONValue) -> AdaptivePlanResult {
  let object = raw.objectValue ?? [:]
  func string(_ key: String) -> String? { if case .string(let value)? = object[key] { return value }; return nil }
  func typed<T: Decodable>(_ type: T.Type, _ value: JSONValue?) -> T? {
    guard let value, value != .null, let data = try? JSONEncoder().encode(value) else { return nil }
    return try? JSONDecoder().decode(type, from: data)
  }
  let decisions = object["decisions"].flatMap { typed([CoachDecision].self, $0) } ?? []
  return AdaptivePlanResult(status: string("status") ?? "invalid_input",
    currentPlan: typed(WorkoutPlan.self, object["currentPlan"]),
    proposedPlan: typed(WorkoutPlan.self, object["proposedPlan"]), decisions: decisions,
    currentEvaluation: typed(PlanEvaluation.self, object["currentEvaluation"]),
    proposedEvaluation: typed(PlanEvaluation.self, object["proposedEvaluation"]),
    trainingState: typed(TrainingState.self, object["trainingState"]),
    changes: applicationChanges(object["changes"]), unresolvedIssues: applicationIssues(object["unresolvedIssues"]),
    provenance: object["provenance"]?.objectValue ?? [:])
}

// MARK: - Typed TrainingEngine facade

public extension TrainingEngine {
  /// Validates an intent without throwing for normal domain invalidity.
  func validateIntent(_ intent: WorkoutIntent) -> IntentValidationResult {
    let errors = FreeExerciseDBPlusPlus.validateWorkoutIntent(intent, database: database, relationships: relationships)
    let issues = errors.map { error -> IntentValidationIssue in
      let parts = error.split(separator: ":", maxSplits: 1).map(String.init)
      let field = parts.count == 2 ? parts[0] : nil
      let normalized = error.trimmingCharacters(in: .whitespaces).uppercased()
      let code: String
      if normalized == "GOAL_POLICY_MISMATCH" { code = normalized }
      else if normalized.contains("UNKNOWN EXERCISEID") { code = "UNKNOWN_EXERCISE_ID" }
      else if normalized.contains("UNKNOWN DB++ EQUIPMENT") { code = "UNKNOWN_EQUIPMENT" }
      else if normalized.contains("UNKNOWN FAMILYID") { code = "UNKNOWN_FAMILY_ID" }
      else if normalized.contains("CONFLICT") { code = "CONFLICT" }
      else if normalized.contains("REQUIRE CYCLELENGTHDAYS") || normalized.contains("WEEKDAY FIELDS") { code = "INVALID_WEEKDAY_SCHEDULE" }
      else if normalized.contains("UNKNOWN PLANNING POLICY") { code = "UNKNOWN_PLANNING_POLICY" }
      else { code = "INVALID_INTENT" }
      return IntentValidationIssue(code: code, field: field, message: error)
    }
    return IntentValidationResult(status: issues.isEmpty ? IntentValidationResult.validStatus : IntentValidationResult.invalidStatus, issues: issues)
  }

  /// Resolves a typed intent and typed optional context. `Date` is converted
  /// once to a stable ISO-8601 instant; no current time is read by the engine.
  func resolveIntent(_ intent: WorkoutIntent, profile: TrainingProfile? = nil,
                     target: VolumeTarget? = nil, history: TrainingHistory? = nil,
                     asOf: Date? = nil) -> IntentResolutionResult {
    let profileJSON = profile.flatMap(applicationJSON)
    let targetJSON = target.flatMap(applicationJSON)
    let historyJSON = history.flatMap(applicationJSON)
    return FreeExerciseDBPlusPlus.resolveIntent(intent, database: database, profile: profileJSON,
                         target: targetJSON, relationships: relationships,
                         history: historyJSON, asOf: applicationDate(asOf))
  }

  /// Generates a PLAN from strongly typed request values.
  func generatePlan(request: PlanGenerationRequest) -> GeneratedPlanResult {
    guard let profile = applicationJSON(request.profile), let target = applicationJSON(request.target) else {
      return GeneratedPlanResult(status: "invalid_input", unsatisfiedConstraints: [PlanIssue(code: "INVALID_INPUT")])
    }
    let raw = generatePlan(profile: profile, target: target, policy: request.policy,
      trainingState: request.trainingState.flatMap(applicationJSON),
      currentPlan: request.currentPlan.flatMap(applicationJSON),
      requiredExerciseIds: request.requiredExerciseIds, lockedExerciseIds: request.lockedExerciseIds,
      requiredFamilyIds: request.requiredFamilyIds, additionalExclusions: request.additionalExclusions)
    return applicationGenerated(raw)
  }

  /// Resolves an intent and generates a typed PLAN result. An invalid or
  /// incomplete intent returns a structured result with no partial PLAN.
  func generatePlanFromIntent(_ intent: WorkoutIntent, profile: TrainingProfile? = nil,
                              target: VolumeTarget? = nil, history: TrainingHistory? = nil,
                              currentPlan: WorkoutPlan? = nil, asOf: Date? = nil) -> IntentPlanResult {
    let raw = FreeExerciseDBPlusPlus.generatePlanFromIntent(intent, database: database,
      profile: profile.flatMap(applicationJSON), target: target.flatMap(applicationJSON),
      relationships: relationships, history: history.flatMap(applicationJSON),
      currentPlan: currentPlan.flatMap(applicationJSON), asOf: applicationDate(asOf))
    let object = raw.objectValue ?? [:]
    let resolutionData = (try? JSONEncoder().encode(object["resolution"] ?? .object([:])))
    let resolution = resolutionData.flatMap { try? JSONDecoder().decode(IntentResolutionResult.self, from: $0) }
      ?? IntentResolutionResult(status: "invalid_input")
    let generation = object["generation"].map { applicationGenerated($0) }
    let result = IntentPlanResult(resolution: resolution, generation: generation)
    // Keep the explicit current plan meaningful for a caller using continuity:
    // the canonical resolver already owns the semantic path, so no second
    // generation is attempted here.
    _ = currentPlan
    return result
  }

  /// Evaluates a typed PLAN and returns a strongly typed result model.
  func evaluatePlan(_ plan: WorkoutPlan, profile: TrainingProfile? = nil,
                    target: VolumeTarget? = nil) -> PlanEvaluation {
    guard let planJSON = applicationJSON(plan) else { return PlanEvaluation(document: .object(["summary": .object(["evaluationStatus": .string("invalid_input")])])) }
    return PlanEvaluation(document: FreeExerciseDBPlusPlus.evaluatePlan(planJSON, database: database,
      profile: profile.flatMap(applicationJSON), target: target.flatMap(applicationJSON), relationships: relationships))
  }

  /// Derives a typed state from typed history at an explicit instant.
  func deriveTrainingState(history: TrainingHistory, asOf: Date,
                           window: TrainingHistoryWindow? = nil,
                           target: VolumeTarget? = nil) throws -> TrainingState {
    guard let historyJSON = applicationJSON(history), let timestamp = applicationDate(asOf) else {
      throw FEDBError.invalidDocument("unable to encode typed history")
    }
    let raw = FreeExerciseDBPlusPlus.deriveTrainingState(historyJSON, asOf: timestamp,
      window: window ?? .last28Days, relationships: relationships, database: database)
    return try JSONDecoder().decode(TrainingState.self, from: JSONEncoder().encode(raw))
  }

  /// Returns deterministic advisory progression decisions for each matching
  /// prescription in a PLAN/history state pair.
  func suggestProgression(plan: WorkoutPlan, state: TrainingState,
                          policy: String = "double-progression-v1") -> [CoachDecision] {
    guard let planJSON = applicationJSON(plan), let stateJSON = applicationJSON(state) else { return [] }
    let decisions = plan.sessions.flatMap { session in session.exercises.compactMap { prescription -> CoachDecision? in
      guard let prescriptionJSON = applicationJSON(prescription),
            let rawState = stateJSON.objectValue?["exerciseState"]?.objectValue?[prescription.exerciseId ?? ""] else { return nil }
      let raw = applyProgressionPolicy(policy, prescription: prescriptionJSON, exerciseState: rawState)
      return try? JSONDecoder().decode(CoachDecision.self, from: JSONEncoder().encode(raw))
    }}
    _ = planJSON
    return decisions.sorted { ($0.prescriptionId ?? "", $0.decisionType) < ($1.prescriptionId ?? "", $1.decisionType) }
  }

  /// Applies adaptive coaching to a typed request without mutating the input.
  func adaptPlan(request: PlanAdaptationRequest) -> AdaptivePlanResult {
    guard let profile = applicationJSON(request.profile), let target = applicationJSON(request.target),
          let current = applicationJSON(request.currentPlan) else {
      return AdaptivePlanResult(status: "invalid_input", unresolvedIssues: [PlanIssue(code: "INVALID_INPUT")])
    }
    let state = request.trainingState.flatMap(applicationJSON)
    let raw = FreeExerciseDBPlusPlus.adaptPlan(profile: profile, target: target, currentPlan: current,
      history: request.history.flatMap(applicationJSON), asOf: applicationDate(request.asOf),
      trainingState: state, database: database, policy: request.policy,
      planningPolicy: request.planningPolicy, relationships: relationships)
    return applicationAdaptive(raw)
  }
}
