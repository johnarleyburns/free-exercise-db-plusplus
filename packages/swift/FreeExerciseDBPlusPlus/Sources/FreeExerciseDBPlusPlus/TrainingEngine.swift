import Foundation

/// The primary offline, Foundation-only DB++ domain engine.
///
/// `TrainingEngine` owns the exercise database, relationships, policies, and
/// deterministic PLAN/ACTUAL/TARGET operations. It has no Python, subprocess,
/// network, UIKit, SwiftUI, AppKit, or Foundation Models dependency. Use
/// `bundled()` for the package's offline resources or initialize it with a
/// custom database for tests and specialized deployments.
public struct TrainingEngine: Sendable {
  public let database: FEDatabase
  public let relationships: ExerciseRelationships?
  private let indexes: TrainingEngineIndexes

  public init(database: FEDatabase, relationships: ExerciseRelationships? = nil) {
    self.database = database
    self.relationships = relationships
    self.indexes = TrainingEngineIndexes(database: database, relationships: relationships)
  }

  /// Deterministic, immutable lookup views retained for the lifetime of the
  /// engine. These are deliberately private so callers cannot mutate or
  /// accidentally depend on implementation storage.
  private struct TrainingEngineIndexes: Sendable {
    let exerciseByID: [String: Exercise]
    let exercisesByMuscle: [String: [String]]
    let exercisesByMovementPattern: [String: [String]]
    let exercisesByEquipment: [String: [String]]
    let familyMembersByID: [String: [String]]

    init(database: FEDatabase, relationships: ExerciseRelationships?) {
      let exercises = database.allExercises.values.sorted { $0.exerciseId < $1.exerciseId }
      self.exerciseByID = Dictionary(uniqueKeysWithValues: exercises.map { ($0.exerciseId, $0) })
      self.exercisesByMuscle = Dictionary(grouping: exercises.flatMap { exercise in
        Set(exercise.annotation.direct + exercise.annotation.indirect + exercise.annotation.stabilizers)
          .map { ($0, exercise.exerciseId) }
      }, by: { $0.0 }).mapValues { $0.map(\.1).sorted() }
      self.exercisesByMovementPattern = Dictionary(grouping: exercises.flatMap { exercise in
        exercise.annotation.patterns.map { ($0, exercise.exerciseId) }
      }, by: { $0.0 }).mapValues { $0.map(\.1).sorted() }
      self.exercisesByEquipment = Dictionary(grouping: exercises.compactMap { exercise -> (String, String)? in
        guard case .string(let equipment) = exercise.source?["equipment"] else { return nil }
        return (equipment, exercise.exerciseId)
      }, by: { $0.0 }).mapValues { $0.map(\.1).sorted() }
      self.familyMembersByID = Dictionary(uniqueKeysWithValues: (relationships?.families.keys.sorted() ?? []).map { familyID in
        (familyID, relationships?.members(of: familyID) ?? [])
      })
    }
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

  @available(*, deprecated, message: "Use the typed resolveIntent(_:profile:target:history:asOf:) overload or the global compatibility function.")
  public func resolveIntentJSON(_ intent: WorkoutIntent, profile: JSONValue? = nil, target: JSONValue? = nil, history: JSONValue? = nil, asOf: String? = nil) -> IntentResolutionResult {
    IntentResolver().resolve(intent, database: database, profile: profile, target: target, relationships: relationships, history: history, asOf: asOf)
  }

  public func evaluatePlan(_ plan: JSONValue, profile: JSONValue? = nil, target: JSONValue? = nil) -> JSONValue {
    FreeExerciseDBPlusPlus.evaluatePlan(plan, database: database, profile: profile, target: target, relationships: relationships)
  }

  public func applyProgressionPolicy(_ policy: String, prescription: JSONValue, exerciseState: JSONValue, parameters: JSONValue? = nil) -> JSONValue {
    FreeExerciseDBPlusPlus.applyProgressionPolicy(policy, prescription: prescription, exerciseState: exerciseState, parameters: parameters)
  }

  /// Generate a production-equivalent PLAN result using the native database,
  /// relationships, evaluator, and deterministic planning policy.
  public func generatePlan(profile: JSONValue, target: JSONValue,
                           policy: String = "full-body-general-v1",
                           trainingState: JSONValue? = nil,
                           currentPlan: JSONValue? = nil,
                           requiredExerciseIds: [String] = [],
                           lockedExerciseIds: [String] = [],
                           requiredFamilyIds: [String] = [],
                           additionalExclusions: [String] = [],
                           options: JSONValue? = nil) -> JSONValue {
    FreeExerciseDBPlusPlus.generatePlan(profile: profile, target: target, database: database,
      policy: policy, relationships: relationships, trainingState: trainingState,
      currentPlan: currentPlan, requiredExerciseIds: requiredExerciseIds,
      lockedExerciseIds: lockedExerciseIds, requiredFamilyIds: requiredFamilyIds,
      additionalExclusions: additionalExclusions,
      options: options)
  }

  /// Return the immutable released planning-policy document used by the
  /// native generator, or nil for an unknown policy identifier.
  public func planningPolicy(_ policy: String) -> JSONValue? {
    FreeExerciseDBPlusPlus.planningPolicy(policy)
  }

  public func goalPolicy(_ policy: String) -> JSONValue? {
    FreeExerciseDBPlusPlus.goalPolicy(policy)
  }

  public func coachingPolicy(_ policy: String = "general-adaptive-v1") -> JSONValue? {
    FreeExerciseDBPlusPlus.coachingPolicy(policy)
  }

  public func adaptPlan(profile: JSONValue, target: JSONValue, currentPlan: JSONValue,
                        history: JSONValue? = nil, asOf: String? = nil,
                        trainingState: JSONValue? = nil, policy: String = "general-adaptive-v1",
                        planningPolicy: String? = nil) -> JSONValue {
    FreeExerciseDBPlusPlus.adaptPlan(profile: profile, target: target, currentPlan: currentPlan,
      history: history, asOf: asOf, trainingState: trainingState, database: database,
      policy: policy, planningPolicy: planningPolicy, relationships: relationships)
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
  @available(*, deprecated, message: "Use the typed generatePlanFromIntent(_:profile:target:history:currentPlan:asOf:) overload or the global compatibility function.")
  public func generatePlanFromIntentJSON(
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
