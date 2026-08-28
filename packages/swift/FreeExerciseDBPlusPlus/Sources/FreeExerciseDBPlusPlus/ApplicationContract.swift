import Foundation

/// Explicit application operation. DB++ never infers generation versus
/// adaptation from the fields present in a request.
public enum TrainingOperation: String, Codable, Sendable, Equatable {
  case resolveIntent = "resolve_intent"
  case generateFromIntent = "generate_from_intent"
  case generatePlan = "generate_plan"
  case evaluatePlan = "evaluate_plan"
  case deriveState = "derive_state"
  case suggestProgression = "suggest_progression"
  case adaptPlan = "adapt_plan"
}

/// Transport-neutral request envelope. Canonical domain objects remain typed;
/// `options` is reserved for policy-specific extension fields.
public struct TrainingRequest: Codable, Sendable, Equatable {
  public let schemaVersion: String
  public let requestId: String
  public let operation: TrainingOperation
  public let intent: WorkoutIntent?
  public let profile: TrainingProfile?
  public let target: VolumeTarget?
  public let history: TrainingHistory?
  public let trainingState: TrainingState?
  public let currentPlan: WorkoutPlan?
  public let plan: WorkoutPlan?
  public let asOf: String?
  public let historyWindow: TrainingHistoryWindow?
  public let options: [String: JSONValue]

  public init(schemaVersion: String = "0.1.0", requestId: String,
              operation: TrainingOperation, intent: WorkoutIntent? = nil,
              profile: TrainingProfile? = nil, target: VolumeTarget? = nil,
              history: TrainingHistory? = nil, trainingState: TrainingState? = nil,
              currentPlan: WorkoutPlan? = nil, plan: WorkoutPlan? = nil,
              asOf: String? = nil, historyWindow: TrainingHistoryWindow? = nil,
              options: [String: JSONValue] = [:]) {
    self.schemaVersion = schemaVersion; self.requestId = requestId; self.operation = operation
    self.intent = intent; self.profile = profile; self.target = target; self.history = history
    self.trainingState = trainingState; self.currentPlan = currentPlan; self.plan = plan
    self.asOf = asOf; self.historyWindow = historyWindow; self.options = options
  }

  private enum CodingKeys: String, CodingKey {
    case schemaVersion, requestId, operation, intent, profile, target, history,
      trainingState, currentPlan, plan, asOf, historyWindow, options
  }

  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    schemaVersion = try c.decodeIfPresent(String.self, forKey: .schemaVersion) ?? "0.1.0"
    requestId = try c.decode(String.self, forKey: .requestId)
    operation = try c.decode(TrainingOperation.self, forKey: .operation)
    intent = try c.decodeIfPresent(WorkoutIntent.self, forKey: .intent)
    profile = try c.decodeIfPresent(TrainingProfile.self, forKey: .profile)
    target = try c.decodeIfPresent(VolumeTarget.self, forKey: .target)
    history = try c.decodeIfPresent(TrainingHistory.self, forKey: .history)
    trainingState = try c.decodeIfPresent(TrainingState.self, forKey: .trainingState)
    currentPlan = try c.decodeIfPresent(WorkoutPlan.self, forKey: .currentPlan)
    plan = try c.decodeIfPresent(WorkoutPlan.self, forKey: .plan)
    asOf = try c.decodeIfPresent(String.self, forKey: .asOf)
    historyWindow = try c.decodeIfPresent(TrainingHistoryWindow.self, forKey: .historyWindow)
    options = try c.decodeIfPresent([String: JSONValue].self, forKey: .options) ?? [:]
  }
}

/// One stable result envelope for all application operations.
public struct TrainingResult: Codable, Sendable, Equatable {
  public let schemaVersion: String
  public let requestId: String
  public let operation: TrainingOperation
  public let status: String
  public let resolution: IntentResolutionResult?
  public let plan: WorkoutPlan?
  public let evaluation: PlanEvaluation?
  public let trainingState: TrainingState?
  public let coachDecisions: [CoachDecision]
  public let adaptation: AdaptivePlanResult?
  public let missingInformation: [MissingInformation]
  public let conflicts: [IntentConflict]
  public let warnings: [String]
  public let issues: [PlanIssue]
  public let provenance: [String: JSONValue]

  public init(schemaVersion: String = "0.1.0", requestId: String,
              operation: TrainingOperation, status: String,
              resolution: IntentResolutionResult? = nil, plan: WorkoutPlan? = nil,
              evaluation: PlanEvaluation? = nil, trainingState: TrainingState? = nil,
              coachDecisions: [CoachDecision] = [], adaptation: AdaptivePlanResult? = nil,
              missingInformation: [MissingInformation] = [], conflicts: [IntentConflict] = [],
              warnings: [String] = [], issues: [PlanIssue] = [],
              provenance: [String: JSONValue] = [:]) {
    self.schemaVersion = schemaVersion; self.requestId = requestId; self.operation = operation
    self.status = status; self.resolution = resolution; self.plan = plan; self.evaluation = evaluation
    self.trainingState = trainingState; self.coachDecisions = coachDecisions; self.adaptation = adaptation
    self.missingInformation = missingInformation; self.conflicts = conflicts; self.warnings = warnings
    self.issues = issues; self.provenance = provenance
  }

  private enum CodingKeys: String, CodingKey {
    case schemaVersion, requestId, operation, status, resolution, plan, evaluation,
      trainingState, coachDecisions, adaptation, missingInformation, conflicts,
      warnings, issues, provenance
  }

  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    schemaVersion = try c.decodeIfPresent(String.self, forKey: .schemaVersion) ?? "0.1.0"
    requestId = try c.decode(String.self, forKey: .requestId)
    operation = try c.decode(TrainingOperation.self, forKey: .operation)
    status = try c.decode(String.self, forKey: .status)
    resolution = try c.decodeIfPresent(IntentResolutionResult.self, forKey: .resolution)
    plan = try c.decodeIfPresent(WorkoutPlan.self, forKey: .plan)
    evaluation = try c.decodeIfPresent(PlanEvaluation.self, forKey: .evaluation)
    trainingState = try c.decodeIfPresent(TrainingState.self, forKey: .trainingState)
    coachDecisions = try c.decodeIfPresent([CoachDecision].self, forKey: .coachDecisions) ?? []
    adaptation = try c.decodeIfPresent(AdaptivePlanResult.self, forKey: .adaptation)
    missingInformation = try c.decodeIfPresent([MissingInformation].self, forKey: .missingInformation) ?? []
    conflicts = try c.decodeIfPresent([IntentConflict].self, forKey: .conflicts) ?? []
    warnings = try c.decodeIfPresent([String].self, forKey: .warnings) ?? []
    issues = try c.decodeIfPresent([PlanIssue].self, forKey: .issues) ?? []
    provenance = try c.decodeIfPresent([String: JSONValue].self, forKey: .provenance) ?? [:]
  }

  public func encode(to encoder: Encoder) throws {
    var c = encoder.container(keyedBy: CodingKeys.self)
    try c.encode(schemaVersion, forKey: .schemaVersion); try c.encode(requestId, forKey: .requestId)
    try c.encode(operation, forKey: .operation); try c.encode(status, forKey: .status)
    try c.encode(resolution, forKey: .resolution); try c.encode(plan, forKey: .plan)
    try c.encode(evaluation, forKey: .evaluation); try c.encode(trainingState, forKey: .trainingState)
    try c.encode(coachDecisions, forKey: .coachDecisions); try c.encode(adaptation, forKey: .adaptation)
    try c.encode(missingInformation, forKey: .missingInformation); try c.encode(conflicts, forKey: .conflicts)
    try c.encode(warnings, forKey: .warnings); try c.encode(issues, forKey: .issues)
    try c.encode(provenance, forKey: .provenance)
  }
}

private extension TrainingRequest {
  var optionStrings: [String: String] {
    options.compactMapValues { value in if case .string(let text) = value { return text }; return nil }
  }

  func optionStringArray(_ key: String) -> [String] {
    guard case .array(let values)? = options[key] else { return [] }
    return values.compactMap { value in
      if case .string(let text) = value { return text }
      return nil
    }
  }
}

public extension TrainingEngine {
  /// Processes one explicit application request through the existing
  /// deterministic engine. Domain failures are returned as statuses; throws
  /// are reserved for malformed typed documents or unavailable resources.
  func processTrainingRequest(_ request: TrainingRequest) throws -> TrainingResult {
    guard request.schemaVersion == "0.1.0", !request.requestId.isEmpty else {
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: "invalid", issues: [PlanIssue(code: "INVALID_REQUEST")])
    }
    func invalid(_ code: String) -> TrainingResult {
      TrainingResult(requestId: request.requestId, operation: request.operation,
                     status: "invalid", issues: [PlanIssue(code: code)])
    }
    switch request.operation {
    case .resolveIntent:
      guard let intent = request.intent else { return invalid("MISSING_INTENT") }
      let resolution = applicationResolution(
        resolveIntent(intent, profile: request.profile, target: request.target,
                      history: request.history, asOf: parsedDate(request.asOf)), asOf: request.asOf)
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: resolution.status, resolution: resolution,
                            missingInformation: resolution.missingInformation,
                            conflicts: resolution.conflicts, warnings: resolution.warnings,
                            provenance: resolution.provenance)
    case .generateFromIntent:
      guard let intent = request.intent else { return invalid("MISSING_INTENT") }
      let combined = generatePlanFromIntent(intent, profile: request.profile, target: request.target,
                                            history: request.history, currentPlan: request.currentPlan,
                                            asOf: parsedDate(request.asOf))
      let resolution = applicationResolution(combined.resolution, asOf: request.asOf)
      guard let generation = combined.generation else {
        return TrainingResult(requestId: request.requestId, operation: request.operation,
                              status: resolution.status, resolution: resolution,
                              missingInformation: resolution.missingInformation,
                              conflicts: resolution.conflicts, warnings: resolution.warnings,
                              provenance: resolution.provenance)
      }
      let issues = generation.unsatisfiedConstraints + generation.unsatisfiedTargets + generation.unsatisfiedSoftPreferences
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: generation.status, resolution: resolution,
                            plan: generation.plan, evaluation: generation.evaluation,
                            warnings: resolution.warnings, issues: issues, provenance: generation.provenance)
    case .generatePlan:
      guard let profile = request.profile, let target = request.target else { return invalid("MISSING_PROFILE_OR_TARGET") }
      let policy = request.optionStrings["policy"] ?? "full-body-general-v1"
      let generation = generatePlan(request: PlanGenerationRequest(profile: profile, target: target,
                                                                     policy: policy,
                                                                     trainingState: request.trainingState,
                                                                     currentPlan: request.currentPlan,
                                                                     requiredExerciseIds: request.optionStringArray("requiredExerciseIds"),
                                                                     lockedExerciseIds: request.optionStringArray("lockedExerciseIds"),
                                                                     requiredFamilyIds: request.optionStringArray("requiredFamilyIds"),
                                                                     additionalExclusions: request.optionStringArray("additionalExclusions")))
      let issues = generation.unsatisfiedConstraints + generation.unsatisfiedTargets + generation.unsatisfiedSoftPreferences
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: generation.status, plan: generation.plan,
                            evaluation: generation.evaluation, issues: issues,
                            provenance: generation.provenance)
    case .evaluatePlan:
      guard let plan = request.plan else { return invalid("MISSING_PLAN") }
      let evaluation = evaluatePlan(plan, profile: request.profile, target: request.target)
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: "evaluated", plan: plan, evaluation: evaluation,
                            warnings: evaluation.warnings, issues: evaluation.issues,
                            provenance: evaluation.provenance)
    case .deriveState:
      guard let history = request.history, let asOf = request.asOf,
            let window = request.historyWindow else { return invalid("MISSING_HISTORY_OR_AS_OF") }
      guard let historyJSON = applicationJSON(history) else { return invalid("INVALID_HISTORY") }
      var historyObject = historyJSON.objectValue ?? [:]
      if case .string(let timezone)? = request.options["timezone"] { historyObject["timezone"] = .string(timezone) }
      if let target = request.target, let targetJSON = applicationJSON(target) {
        var targets: [JSONValue] = if case .array(let values)? = historyObject["targets"] { values } else { [] }
        targets.append(targetJSON); historyObject["targets"] = .array(targets)
      }
      let rawState = deriveTrainingState(.object(historyObject), asOf: asOf, window: window)
      let state = try JSONDecoder().decode(TrainingState.self,
                                           from: JSONEncoder().encode(rawState))
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: "state_derived", trainingState: state,
                            provenance: state.provenance)
    case .suggestProgression:
      guard let plan = request.plan, let state = request.trainingState else { return invalid("MISSING_PLAN_OR_TRAINING_STATE") }
      let decisions = suggestProgression(plan: plan, state: state,
                                         policy: request.optionStrings["policy"] ?? "double-progression-v1")
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: decisions.isEmpty ? "insufficient_data" : "progression_available",
                            plan: plan, coachDecisions: decisions)
    case .adaptPlan:
      guard let profile = request.profile, let target = request.target,
            let currentPlan = request.currentPlan, let history = request.history,
            let asOf = request.asOf, let date = parsedDate(asOf) else { return invalid("MISSING_ADAPTATION_INPUT") }
      let adapted = adaptPlan(request: PlanAdaptationRequest(profile: profile, target: target,
                                                              currentPlan: currentPlan, history: history,
                                                              asOf: date,
                                                              policy: request.optionStrings["policy"] ?? "general-adaptive-v1",
                                                              planningPolicy: request.optionStrings["planningPolicy"] ?? (evaluatePlan(currentPlan, profile: profile, target: target).summary.satisfiesHardConstraints ? nil : "full-body-general-v1")),
                             canonicalAsOf: canonicalApplicationAsOf(asOf))
      let canonicalAdapted = adapted
      return TrainingResult(requestId: request.requestId, operation: request.operation,
                            status: canonicalAdapted.status, plan: canonicalAdapted.currentPlan,
                            trainingState: canonicalAdapted.trainingState,
                            coachDecisions: canonicalAdapted.decisions, adaptation: canonicalAdapted,
                            issues: canonicalAdapted.unresolvedIssues, provenance: canonicalAdapted.provenance)
    }
  }
}

private func parsedDate(_ value: String?) -> Date? {
  guard let value else { return nil }
  let formatter = ISO8601DateFormatter()
  formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
  return formatter.date(from: value) ?? {
    formatter.formatOptions = [.withInternetDateTime]
    return formatter.date(from: value)
  }()
}

func canonicalApplicationAsOf(_ value: String) -> String {
  value.hasSuffix("Z") ? String(value.dropLast()) + "+00:00" : value
}
