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

  public func resolveIntent(_ intent: WorkoutIntent, profile: JSONValue? = nil, target: JSONValue? = nil, history: JSONValue? = nil, asOf: String? = nil) -> IntentResolutionResult {
    IntentResolver().resolve(intent, database: database, profile: profile, target: target, relationships: relationships, history: history, asOf: asOf)
  }

  public func evaluatePlan(_ plan: JSONValue, profile: JSONValue? = nil, target: JSONValue? = nil) -> JSONValue {
    FreeExerciseDBPlusPlus.evaluatePlan(plan, database: database, profile: profile, target: target, relationships: relationships)
  }

  public func deriveTrainingState(_ history: JSONValue, asOf: String) -> JSONValue {
    FreeExerciseDBPlusPlus.deriveTrainingState(history, asOf: asOf)
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
