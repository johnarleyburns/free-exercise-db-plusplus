import XCTest
@testable import FreeExerciseDBPlusPlus

final class ApplicationAPITests: XCTestCase {
  func testTypedFacadeSupportsPlanStateAndAdaptiveRoundTrips() throws {
    let engine = try TrainingEngine.bundled()
    let intent = WorkoutIntent(
      goal: "hypertrophy", environment: "commercial_gym",
      schedule: WorkoutSchedule(cycleLengthDays: 7, sessionsPerCycle: IntRange(target: 3)),
      sessionConstraints: SessionConstraints(exercisesPerSession: IntRange(min: 2, max: 4)))
    XCTAssertTrue(engine.validateIntent(intent).isValid)

    let resolution = engine.resolveIntent(intent)
    XCTAssertTrue(["resolved", "resolved_with_defaults"].contains(resolution.status))
    let profile = try decode(TrainingProfile.self, value: try XCTUnwrap(resolution.resolvedProfile))
    let target = try decode(VolumeTarget.self, value: try XCTUnwrap(resolution.resolvedTarget))
    let generated = engine.generatePlan(request: PlanGenerationRequest(profile: profile, target: target))
    XCTAssertEqual(generated.status, "generated")
    let plan = try XCTUnwrap(generated.plan)
    XCTAssertEqual(engine.evaluatePlan(plan, profile: profile, target: target).status, generated.evaluation?.status)

    let combined = engine.generatePlanFromIntent(intent)
    XCTAssertEqual(combined.resolution.status, resolution.status)
    XCTAssertNotNil(combined.generation?.plan)

    let history = TrainingHistory(subjectId: "typed-user", plans: [plan])
    let asOf = try XCTUnwrap(ISO8601DateFormatter().date(from: "2026-08-27T12:00:00Z"))
    let state = try engine.deriveTrainingState(history: history, asOf: asOf)
    XCTAssertEqual(state.subjectId, "typed-user")
    XCTAssertEqual(try JSONDecoder().decode(TrainingState.self, from: JSONEncoder().encode(state)), state)

    let adapted = engine.adaptPlan(request: PlanAdaptationRequest(profile: profile, target: target, currentPlan: plan, history: history, asOf: asOf))
    XCTAssertEqual(adapted.currentPlan, plan)
    let adaptedRoundTrip = try JSONDecoder().decode(AdaptivePlanResult.self, from: JSONEncoder().encode(adapted))
    XCTAssertEqual(adaptedRoundTrip, adapted)
  }

  func testTypedValidationAndUnsatisfiableGenerationAreStructured() throws {
    let engine = try TrainingEngine.bundled()
    let incomplete = engine.resolveIntent(WorkoutIntent())
    XCTAssertEqual(incomplete.status, "needs_clarification")
    XCTAssertFalse(incomplete.missingInformation.isEmpty)

    let profile = TrainingProfile(profileId: "home", availability: TrainingAvailability(cycleLengthDays: 7, sessionsPerCycle: TargetRange(target: 1)), equipment: ["body only"])
    let target = VolumeTarget(targetId: "t", periodDays: 7, muscles: ["chest": TargetRange(target: 2)])
    let request = PlanGenerationRequest(profile: profile, target: target, requiredExerciseIds: ["Barbell_Bench_Press_-_Medium_Grip"])
    let result = engine.generatePlan(request: request)
    XCTAssertEqual(result.status, "unsatisfiable")
    XCTAssertTrue(result.plan == nil)
    XCTAssertFalse(result.unsatisfiedConstraints.isEmpty)
  }

  func testTypedEvaluationUsesCustomSetCreditsAndArbitraryCycle() throws {
    let exercise = Exercise(exerciseId: "custom", annotation: ExerciseAnnotation(direct: ["chest"], volumeEligible: true), source: ["equipment": .string("body only")])
    let database = FEDatabase(metadata: ["setCredits": .object(["direct": .number(2), "indirect": .number(0.25), "stabilizer": .number(0)])], exercises: ["custom": exercise])
    let engine = TrainingEngine(database: database)
    let prescription = PlanExercisePrescription(prescriptionId: "rx", exerciseId: "custom", sets: .number(2), reps: .number(8))
    let plan = WorkoutPlan(planId: "p", revisionId: "r1", cycle: PlanCycle(lengthDays: 11), sessions: [PlanSession(planSessionId: "s", dayOffset: 0, exercises: [prescription])])
    let target = VolumeTarget(targetId: "t", periodDays: 11, muscles: ["chest": TargetRange(min: 4, target: 4, max: 4)])
    let profile = TrainingProfile(profileId: "home", equipment: ["body only"])
    let evaluation = engine.evaluatePlan(plan, profile: profile, target: target)
    XCTAssertEqual(evaluation.muscleCoverage["chest"]?.actualEffectiveSets, 4)
    XCTAssertEqual(evaluation.status, "valid")
  }

  private func decode<T: Decodable>(_ type: T.Type, value: JSONValue) throws -> T {
    try JSONDecoder().decode(type, from: JSONEncoder().encode(value))
  }
}
