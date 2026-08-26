import XCTest

@testable import FreeExerciseDBPlusPlus

final class FreeExerciseDBPlusPlusTests: XCTestCase {
  func testDatabaseLoadsAndQueries() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let db = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
    XCTAssertGreaterThan(db.count, 800)
    XCTAssertEqual(try db.getExercise("Bench_Dips").exerciseId, "Bench_Dips")
    XCTAssertFalse(db.findExercises(containing: "bench").isEmpty)
  }
  func testEffectiveSets() throws {
    let ex = Exercise(
      exerciseId: "x",
      annotation: ExerciseAnnotation(
        direct: ["chest"], indirect: ["triceps"], volumeEligible: true), source: nil)
    let db = FEDatabase(exercises: ["x": ex])
    let workout = Workout(
      schemaVersion: "0.2.0", sessionId: "s", startTime: "2026-01-01T00:00:00Z",
      exercises: [
        ExerciseObservation(
          exerciseId: "x", exerciseName: nil, order: 1, laterality: nil,
          sets: [
            SetObservation(setNumber: 1, setType: "working", completed: true),
            SetObservation(setNumber: 2, setType: "working", completed: false),
          ])
      ])
    XCTAssertEqual(workout.effectiveSets(using: db)["chest"], 1)
    XCTAssertEqual(workout.effectiveSets(using: db)["triceps"], 0.5)
  }
  func testRelationshipArtifactLookup() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let relationships = try ExerciseRelationships.load(
      url: root.appendingPathComponent("exercise-relationships.json"))
    XCTAssertEqual(relationships.family(for: "Dumbbell_Bench_Press")?.familyId, "bench_press")
    XCTAssertTrue(
      relationships.members(of: "bench_press").contains("Barbell_Bench_Press_-_Medium_Grip"))
  }
  func testPlanConsumerDecodesPeriodizedPlan() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let plan = try WorkoutPlan.load(
      url: root.appendingPathComponent("examples/plans/periodized-0.2.json"))
    XCTAssertEqual(plan.schemaVersion, "0.2.0")
    XCTAssertEqual(plan.phases?.count, 2)
    XCTAssertEqual(plan.sessions.first?.exercises.first?.plannedSets?.count, 3)
    let prescription = try XCTUnwrap(plan.sessions.first?.exercises.first)
    XCTAssertNil(prescription.load)
    XCTAssertNil(prescription.effort)
    XCTAssertEqual(prescription.setType, "working")
    XCTAssertEqual(prescription.laterality, "bilateral")
    XCTAssertEqual(prescription.notes, "Preserve bar path.")
    XCTAssertNotNil(prescription.progression)
    XCTAssertNotNil(prescription.plannedSets?.first?.effort)
    XCTAssertEqual(prescription.plannedSets?.first?.notes, "Controlled eccentric")
    let roundTrip = try JSONDecoder().decode(WorkoutPlan.self, from: JSONEncoder().encode(plan))
    XCTAssertEqual(roundTrip, plan)
    let database = try FEDatabase.load(
      url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
    let coverage = plan.coverage(using: database)
    XCTAssertEqual(coverage.nativeCycle.effectiveSets["chest"], 5)
    XCTAssertEqual(coverage.normalized7Day.periodDays, 7)
    XCTAssertEqual(Set(coverage.phaseSpecific.keys), Set(["accumulation", "deload"]))
  }

  func testWorkoutIntentResolutionUsesCanonicalWeekdaysAndOverrides() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let url = root.appendingPathComponent(
      "fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")
    let intent = try JSONDecoder().decode(WorkoutIntent.self, from: Data(contentsOf: url))
    let result = resolveIntent(intent)
    XCTAssertEqual(result.status, "resolved_with_defaults")
    XCTAssertEqual(result.goalPolicy?.policyId, "general-hypertrophy-v1")
    XCTAssertEqual(result.environmentPolicy, "commercial-gym-general-v1")
    XCTAssertEqual(result.defaultsApplied, ["goalPolicy", "planningPolicy", "environmentPolicy"])
    XCTAssertEqual(result.explicitOverrides, ExplicitOverrides())
    guard case .object(let profile)? = result.resolvedProfile,
      case .array(let offsets)? = (profile["availability"] ?? .null).objectValue?[
        "preferredDayOffsets"]
    else { return XCTFail("missing resolved day offsets") }
    XCTAssertEqual(offsets, [0, 1, 2, 3, 5].map { .number(Double($0)) })
  }

  func testWorkoutIntentTargetMergeAndValidationPreservePartialRanges() {
    let base: JSONValue = .object([
      "muscles": .object([
        "chest": .object(["min": .number(4), "target": .number(6), "max": .number(8)])
      ]), "frequency": .object(["muscles": .object(["chest": .object(["target": .number(2)])])]),
    ])
    let override: JSONValue = .object([
      "muscles": .object(["chest": .object(["target": .number(7)])]),
      "frequency": .object(["muscles": .object(["chest": .object(["min": .number(1)])])]),
    ])
    let merged = mergeTarget(base, override)
    XCTAssertEqual(
      merged.objectValue?["muscles"]?.objectValue?["chest"]?.objectValue?["min"], .number(4))
    XCTAssertEqual(
      merged.objectValue?["muscles"]?.objectValue?["chest"]?.objectValue?["target"], .number(7))
    XCTAssertEqual(
      merged.objectValue?["muscles"]?.objectValue?["chest"]?.objectValue?["max"], .number(8))
    XCTAssertEqual(
      validateTarget(
        .object([
          "movementPatterns": .object([
            "squat": .object(["minimumSets": .number(4), "targetSets": .number(2)])
          ])
        ])), ["movementPatterns.squat: target must not be below min"])
  }

  func testWorkoutIntentGoalMismatchIsStructured() {
    let intent = WorkoutIntent(
      goal: "hypertrophy", requestedGoalPolicy: "general-strength-v1",
      environment: "commercial_gym",
      schedule: WorkoutSchedule(cycleLengthDays: 7, sessionsPerCycle: IntRange(target: 3)))
    let result = resolveIntent(intent)
    XCTAssertEqual(result.status, "invalid")
    XCTAssertEqual(result.conflicts.first?.code, "GOAL_POLICY_MISMATCH")
    XCTAssertEqual(result.explicitOverrides, ExplicitOverrides())
  }

}
