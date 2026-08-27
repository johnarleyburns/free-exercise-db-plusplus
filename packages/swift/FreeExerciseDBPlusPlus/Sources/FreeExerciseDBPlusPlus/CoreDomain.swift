import Foundation

/// A portable inclusive numeric range.  Missing bounds remain missing.
public struct TargetRange: Codable, Sendable, Equatable {
  public let min: Double?
  public let target: Double?
  public let max: Double?
  public init(min: Double? = nil, target: Double? = nil, max: Double? = nil) {
    self.min = min; self.target = target; self.max = max
  }
  private enum CodingKeys: String, CodingKey { case min, target, max, minimumSets, targetSets, maximumSets }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    min = try c.decodeIfPresent(Double.self, forKey: .min) ?? c.decodeIfPresent(Double.self, forKey: .minimumSets)
    target = try c.decodeIfPresent(Double.self, forKey: .target) ?? c.decodeIfPresent(Double.self, forKey: .targetSets)
    max = try c.decodeIfPresent(Double.self, forKey: .max) ?? c.decodeIfPresent(Double.self, forKey: .maximumSets)
  }
  public func encode(to encoder: Encoder) throws {
    var c = encoder.container(keyedBy: CodingKeys.self)
    try c.encodeIfPresent(min, forKey: .min); try c.encodeIfPresent(target, forKey: .target); try c.encodeIfPresent(max, forKey: .max)
  }
}

public struct VolumeTarget: Codable, Sendable, Equatable {
  public let schemaVersion: String
  public let targetId: String
  public let periodDays: Int
  public let muscles: [String: TargetRange]
  public let frequency: [String: [String: TargetRange]]
  public let movementPatterns: [String: TargetRange]
  public let families: [String: TargetRange]
  public let provenance: JSONValue?
  public init(schemaVersion: String = "0.1.0", targetId: String, periodDays: Int,
              muscles: [String: TargetRange] = [:], frequency: [String: [String: TargetRange]] = [:],
              movementPatterns: [String: TargetRange] = [:], families: [String: TargetRange] = [:],
              provenance: JSONValue? = nil) {
    self.schemaVersion = schemaVersion; self.targetId = targetId; self.periodDays = periodDays
    self.muscles = muscles; self.frequency = frequency; self.movementPatterns = movementPatterns
    self.families = families; self.provenance = provenance
  }
  private enum CodingKeys: String, CodingKey { case schemaVersion, targetId, periodDays, muscles, frequency, movementPatterns, families, provenance }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    schemaVersion = try c.decode(String.self, forKey: .schemaVersion)
    targetId = try c.decode(String.self, forKey: .targetId); periodDays = try c.decode(Int.self, forKey: .periodDays)
    muscles = try c.decodeIfPresent([String: TargetRange].self, forKey: .muscles) ?? [:]
    frequency = try c.decodeIfPresent([String: [String: TargetRange]].self, forKey: .frequency) ?? [:]
    movementPatterns = try c.decodeIfPresent([String: TargetRange].self, forKey: .movementPatterns) ?? [:]
    families = try c.decodeIfPresent([String: TargetRange].self, forKey: .families) ?? [:]
    provenance = try c.decodeIfPresent(JSONValue.self, forKey: .provenance)
  }
}

public struct TrainingAvailability: Codable, Sendable, Equatable {
  public var cycleLengthDays: Int?
  public var sessionsPerCycle: TargetRange?
  public var minutesPerSession: TargetRange?
  public var exercisesPerSession: TargetRange?
  public var preferredDayOffsets: [Int]
  public var excludedDayOffsets: [Int]
  public init(cycleLengthDays: Int? = nil, sessionsPerCycle: TargetRange? = nil,
              minutesPerSession: TargetRange? = nil, exercisesPerSession: TargetRange? = nil,
              preferredDayOffsets: [Int] = [], excludedDayOffsets: [Int] = []) {
    self.cycleLengthDays = cycleLengthDays; self.sessionsPerCycle = sessionsPerCycle
    self.minutesPerSession = minutesPerSession; self.exercisesPerSession = exercisesPerSession
    self.preferredDayOffsets = preferredDayOffsets; self.excludedDayOffsets = excludedDayOffsets
  }
  private enum CodingKeys: String, CodingKey { case cycleLengthDays, sessionsPerCycle, minutesPerSession, exercisesPerSession, preferredDayOffsets, excludedDayOffsets }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    cycleLengthDays = try c.decodeIfPresent(Int.self, forKey: .cycleLengthDays)
    sessionsPerCycle = try c.decodeIfPresent(TargetRange.self, forKey: .sessionsPerCycle)
    minutesPerSession = try c.decodeIfPresent(TargetRange.self, forKey: .minutesPerSession)
    exercisesPerSession = try c.decodeIfPresent(TargetRange.self, forKey: .exercisesPerSession)
    preferredDayOffsets = try c.decodeIfPresent([Int].self, forKey: .preferredDayOffsets) ?? []
    excludedDayOffsets = try c.decodeIfPresent([Int].self, forKey: .excludedDayOffsets) ?? []
  }
}

public struct TrainingProfile: Codable, Sendable, Equatable {
  public let schemaVersion: String
  public let profileId: String?
  public let goals: [JSONValue]
  public let experience: String?
  public let availability: TrainingAvailability?
  public let equipment: [String]
  public let exercisePreferences: [String: JSONValue]
  public let constraints: [String: JSONValue]
  public let extensions: [String: JSONValue]
  public init(schemaVersion: String = "0.1.0", profileId: String? = nil, goals: [JSONValue] = [],
              experience: String? = nil, availability: TrainingAvailability? = nil,
              equipment: [String] = [], exercisePreferences: [String: JSONValue] = [:],
              constraints: [String: JSONValue] = [:], extensions: [String: JSONValue] = [:]) {
    self.schemaVersion = schemaVersion; self.profileId = profileId; self.goals = goals
    self.experience = experience; self.availability = availability; self.equipment = equipment
    self.exercisePreferences = exercisePreferences; self.constraints = constraints; self.extensions = extensions
  }
  private enum CodingKeys: String, CodingKey { case schemaVersion, profileId, goals, experience, availability, equipment, exercisePreferences, constraints, extensions }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    schemaVersion = try c.decode(String.self, forKey: .schemaVersion); profileId = try c.decodeIfPresent(String.self, forKey: .profileId)
    goals = try c.decodeIfPresent([JSONValue].self, forKey: .goals) ?? []; experience = try c.decodeIfPresent(String.self, forKey: .experience)
    availability = try c.decodeIfPresent(TrainingAvailability.self, forKey: .availability); equipment = try c.decodeIfPresent([String].self, forKey: .equipment) ?? []
    exercisePreferences = try c.decodeIfPresent([String: JSONValue].self, forKey: .exercisePreferences) ?? [:]
    constraints = try c.decodeIfPresent([String: JSONValue].self, forKey: .constraints) ?? [:]
    extensions = try c.decodeIfPresent([String: JSONValue].self, forKey: .extensions) ?? [:]
  }
}

public struct PlanActivation: Codable, Sendable, Equatable {
  public let planId: String
  public let revisionId: String
  public let effectiveFrom: String
  public let effectiveTo: String?
  public init(planId: String, revisionId: String, effectiveFrom: String, effectiveTo: String? = nil) {
    self.planId = planId; self.revisionId = revisionId; self.effectiveFrom = effectiveFrom; self.effectiveTo = effectiveTo
  }
}

/// A scheduled plan occurrence is intentionally date-string based here; timezone-aware chronology is Part L.
public struct ScheduledOccurrence: Codable, Sendable, Equatable {
  public let planId: String
  public let revisionId: String
  public let planSessionId: String
  public let scheduledDate: String
  public init(planId: String, revisionId: String, planSessionId: String, scheduledDate: String) {
    self.planId = planId; self.revisionId = revisionId; self.planSessionId = planSessionId; self.scheduledDate = scheduledDate
  }
}

public struct TrainingHistory: Codable, Sendable, Equatable {
  public let subjectId: String
  public let plans: [WorkoutPlan]
  public let workouts: [Workout]
  public let targets: [VolumeTarget]
  public let planActivations: [PlanActivation]
  public let metadata: [String: JSONValue]
  public init(subjectId: String, plans: [WorkoutPlan] = [], workouts: [Workout] = [], targets: [VolumeTarget] = [], planActivations: [PlanActivation] = [], metadata: [String: JSONValue] = [:]) {
    self.subjectId = subjectId; self.plans = plans; self.workouts = workouts; self.targets = targets; self.planActivations = planActivations; self.metadata = metadata
  }
  private enum CodingKeys: String, CodingKey { case subjectId, plans, workouts, targets, planActivations, metadata }
  public init(from decoder: Decoder) throws {
    let c = try decoder.container(keyedBy: CodingKeys.self)
    subjectId = try c.decode(String.self, forKey: .subjectId)
    plans = try c.decodeIfPresent([WorkoutPlan].self, forKey: .plans) ?? []
    workouts = try c.decodeIfPresent([Workout].self, forKey: .workouts) ?? []
    targets = try c.decodeIfPresent([VolumeTarget].self, forKey: .targets) ?? []
    planActivations = try c.decodeIfPresent([PlanActivation].self, forKey: .planActivations) ?? []
    metadata = try c.decodeIfPresent([String: JSONValue].self, forKey: .metadata) ?? [:]
  }
  public func plan(planId: String, revisionId: String? = nil) -> WorkoutPlan? { plans.first { $0.planId == planId && (revisionId == nil || $0.revisionId == revisionId) } }
  public func activations(for planId: String? = nil) -> [PlanActivation] { planActivations.filter { planId == nil || $0.planId == planId } }
}

public enum TrainingHistoryWindow: Codable, Sendable, Equatable {
  case last7Days, last28Days, currentPlanCycle, currentPhase
  case custom(start: String, end: String)
  public init(from decoder: Decoder) throws {
    let value = try decoder.singleValueContainer().decode(String.self)
    switch value { case "last_7_days": self = .last7Days; case "last_28_days": self = .last28Days; case "current_plan_cycle": self = .currentPlanCycle; case "current_phase": self = .currentPhase; default: throw DecodingError.dataCorrupted(.init(codingPath: decoder.codingPath, debugDescription: "custom windows require explicit construction")) }
  }
  public func encode(to encoder: Encoder) throws {
    var c = encoder.singleValueContainer()
    switch self { case .last7Days: try c.encode("last_7_days"); case .last28Days: try c.encode("last_28_days"); case .currentPlanCycle: try c.encode("current_plan_cycle"); case .currentPhase: try c.encode("current_phase"); case .custom(let start, let end): try c.encode("\(start)/\(end)") }
  }
}

public struct ExerciseState: Codable, Sendable, Equatable {
  public let exerciseId: String
  public let lastPerformedAt: String?
  public let recentSessionCount: Int
  public let recentCompletedSetCount: Int
  public let substitutionCount: Int
  public let unplannedCount: Int
  public let lastPrescription: JSONValue?
  public let lastActual: JSONValue?
  public let prescriptionAdherence: JSONValue?
  public init(exerciseId: String, lastPerformedAt: String? = nil, recentSessionCount: Int = 0, recentCompletedSetCount: Int = 0, substitutionCount: Int = 0, unplannedCount: Int = 0, lastPrescription: JSONValue? = nil, lastActual: JSONValue? = nil, prescriptionAdherence: JSONValue? = nil) {
    self.exerciseId = exerciseId; self.lastPerformedAt = lastPerformedAt; self.recentSessionCount = recentSessionCount; self.recentCompletedSetCount = recentCompletedSetCount; self.substitutionCount = substitutionCount; self.unplannedCount = unplannedCount; self.lastPrescription = lastPrescription; self.lastActual = lastActual; self.prescriptionAdherence = prescriptionAdherence
  }
}

public struct TrainingState: Codable, Sendable, Equatable {
  public let stateVersion: String
  public let subjectId: String
  public let asOf: String
  public let historyWindow: [String: JSONValue]
  public let activePlan: [String: JSONValue]
  public let exerciseState: [String: ExerciseState]
  public let familyState: [String: JSONValue]
  public let muscleState: [String: JSONValue]
  public let adherenceState: [String: JSONValue]
  public let provenance: [String: JSONValue]
  public init(stateVersion: String = "0.1.0", subjectId: String, asOf: String, historyWindow: [String: JSONValue] = [:], activePlan: [String: JSONValue] = [:], exerciseState: [String: ExerciseState] = [:], familyState: [String: JSONValue] = [:], muscleState: [String: JSONValue] = [:], adherenceState: [String: JSONValue] = [:], provenance: [String: JSONValue] = [:]) {
    self.stateVersion = stateVersion; self.subjectId = subjectId; self.asOf = asOf; self.historyWindow = historyWindow; self.activePlan = activePlan; self.exerciseState = exerciseState; self.familyState = familyState; self.muscleState = muscleState; self.adherenceState = adherenceState; self.provenance = provenance
  }
}

public struct CoachDecision: Codable, Sendable, Equatable {
  public let schemaVersion: String
  public let decisionId: String?
  public let decisionType: String
  public let policyId: String
  public let policyVersion: String
  public let planId: String?
  public let revisionId: String?
  public let prescriptionId: String?
  public let exerciseId: String?
  public let before: [String: JSONValue]
  public let after: [String: JSONValue]
  public let reasonCodes: [String]
  public let evidence: [String: JSONValue]
  public let provenance: [String: JSONValue]
}

public struct GeneratedPlanResult: Codable, Sendable, Equatable { public let status: String; public let plan: WorkoutPlan?; public let evaluation: JSONValue?; public let provenance: [String: JSONValue] }
public struct AdaptivePlanResult: Codable, Sendable, Equatable { public let status: String; public let currentPlan: WorkoutPlan?; public let proposedPlan: WorkoutPlan?; public let decisions: [CoachDecision]; public let currentEvaluation: JSONValue?; public let proposedEvaluation: JSONValue? }
public struct IntentPlanResult: Codable, Sendable, Equatable { public let resolution: IntentResolutionResult; public let generation: JSONValue? }
