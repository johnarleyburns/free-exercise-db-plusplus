import Foundation

/// Offline native-engine façade.  Methods are added here only once they are
/// backed by a native canonical implementation; no subprocess or network path
/// is used.
public struct TrainingEngine: Sendable {
  public let database: FEDatabase
  public let relationships: ExerciseRelationships?

  public init(database: FEDatabase, relationships: ExerciseRelationships? = nil) {
    self.database = database
    self.relationships = relationships
  }

  /// Load the canonical offline DB++ artifacts shipped with this Swift
  /// package. Applications do not need to know the repository layout.
  public static func bundled() throws -> TrainingEngine {
    guard let databaseURL = Bundle.module.url(
      forResource: "free-exercise-db-plusplus", withExtension: "json"),
      let relationshipsURL = Bundle.module.url(
        forResource: "exercise-relationships", withExtension: "json")
    else {
      throw FEDBError.invalidDocument("bundled DB++ resources are unavailable")
    }
    return TrainingEngine(
      database: try FEDatabase.load(url: databaseURL),
      relationships: try ExerciseRelationships.load(url: relationshipsURL))
  }

  public func validateWorkoutIntent(_ intent: WorkoutIntent) -> [String] {
    IntentValidator.validate(intent, database: database, relationships: relationships)
  }

  /// Validate a portable TARGET and return stable path-qualified issues.
  public func validateTarget(_ target: JSONValue) -> [String] {
    FreeExerciseDBPlusPlus.validateTarget(target)
  }

  /// Merge an explicit TARGET override without replacing unrelated range
  /// members or nested frequency targets.
  public func mergeTarget(_ base: JSONValue, explicit: JSONValue?) -> JSONValue {
    FreeExerciseDBPlusPlus.mergeTarget(base, explicit)
  }

  public func resolveIntent(_ intent: WorkoutIntent, profile: JSONValue? = nil, target: JSONValue? = nil, history: JSONValue? = nil, asOf: String? = nil) -> IntentResolutionResult {
    IntentResolver().resolve(intent, database: database, profile: profile, target: target, relationships: relationships, history: history, asOf: asOf)
  }

  public func evaluatePlan(_ plan: JSONValue, profile: JSONValue? = nil, target: JSONValue? = nil) -> JSONValue {
    FreeExerciseDBPlusPlus.evaluatePlan(plan, database: database, profile: profile, target: target, relationships: relationships)
  }

  public func deriveTrainingState(_ history: JSONValue, asOf: String) -> JSONValue {
    FreeExerciseDBPlusPlus.deriveTrainingState(history, asOf: asOf, relationships: relationships, database: database)
  }

  public func deriveTrainingState(_ history: JSONValue, asOf: String, window: TrainingHistoryWindow) -> JSONValue {
    FreeExerciseDBPlusPlus.deriveTrainingState(history, asOf: asOf, window: window, relationships: relationships, database: database)
  }

  /// Typed TrainingState façade for callers that already hold canonical history.
  public func deriveTrainingState(_ history: TrainingHistory, asOf: String) throws -> TrainingState {
    let data = try JSONEncoder().encode(history)
    let projected = FreeExerciseDBPlusPlus.deriveTrainingState(try JSONDecoder().decode(JSONValue.self, from: data), asOf: asOf, relationships: relationships, database: database)
    return try JSONDecoder().decode(TrainingState.self, from: JSONEncoder().encode(projected))
  }

  public func deriveTrainingState(_ history: TrainingHistory, asOf: String, window: TrainingHistoryWindow) throws -> TrainingState {
    let data = try JSONEncoder().encode(history)
    let source = try JSONDecoder().decode(JSONValue.self, from: data)
    let projected = FreeExerciseDBPlusPlus.deriveTrainingState(source, asOf: asOf, window: window, relationships: relationships, database: database)
    return try JSONDecoder().decode(TrainingState.self, from: JSONEncoder().encode(projected))
  }

  /// Resolves the uniquely active revision at an instant, independent of input
  /// array order. Explicit workout references are honored by
  /// `resolvePlan(for:in:asOf:)` below.
  public func activePlan(in history: TrainingHistory, asOf: String) throws -> WorkoutPlan? {
    guard let asOf = parseOffsetAwareTimestamp(asOf)?.date else {
      throw FEDBError.invalidDocument("asOf must be an offset-aware ISO-8601 timestamp")
    }
    let candidates = history.plans.filter { plan in
      guard let activation = history.planActivations.first(where: { $0.planId == plan.planId && $0.revisionId == plan.revisionId }),
            let start = parseOffsetAwareTimestamp(activation.effectiveFrom)?.date,
            start <= asOf else { return false }
      if let end = activation.effectiveTo {
        guard let endDate = parseOffsetAwareTimestamp(end)?.date else { return false }
        return asOf < endDate
      }
      return true
    }
    if candidates.count > 1 { throw FEDBError.invalidDocument("overlapping plan activation windows") }
    if let active = candidates.first { return active }
    let referenced = history.workouts.filter { workout in
      guard let stamp = parseOffsetAwareTimestamp(workout.startTime)?.date else { return false }
      return stamp <= asOf
    }.compactMap { workout -> WorkoutPlan? in
      guard let reference = workout.planReference, let planId = reference.planId else { return nil }
      return history.plans.first { $0.planId == planId && (reference.revisionId == nil || $0.revisionId == reference.revisionId) }
    }
    let unique = Dictionary(grouping: referenced, by: { "\($0.planId):\($0.revisionId)" }).values
    return unique.count == 1 ? unique.first?.first : nil
  }

  /// Resolves a workout's plan revision, preferring its explicit reference.
  public func resolvePlan(for workout: Workout, in history: TrainingHistory, asOf: String) throws -> WorkoutPlan? {
    if let reference = workout.planReference, let revisionId = reference.revisionId {
      return history.plans.first { $0.revisionId == revisionId && (reference.planId == nil || $0.planId == reference.planId) }
    }
    return try activePlan(in: history, asOf: asOf)
  }

  /// Resolve intent and construct the current native deterministic draft in a
  /// single application-facing call.  The returned document contains the
  /// resolution and generation sections used by the shared intent fixtures.
  public func generatePlanFromIntent(
    _ intent: WorkoutIntent,
    profile: JSONValue? = nil,
    target: JSONValue? = nil,
    history: JSONValue? = nil,
    asOf: String? = nil
  ) -> JSONValue {
    FreeExerciseDBPlusPlus.generatePlanFromIntent(
      intent, database: database, profile: profile, target: target,
      relationships: relationships, history: history, asOf: asOf)
  }
}
