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
}
