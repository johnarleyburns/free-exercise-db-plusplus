import XCTest

@testable import FreeExerciseDBPlusPlus

final class FreeExerciseDBPlusPlusTests: XCTestCase {
  func testTrainingStateExcludesFutureWorkoutOnSameUTCDate() throws {
        let history: JSONValue = .object([
            "subjectId": .string("s"), "plans": .array([]), "planActivations": .array([]),
            "workouts": .array([
                .object(["startTime": .string("2026-08-25T11:00:00Z"), "exercises": .array([.object(["exerciseId": .string("before"), "sets": .array([.object(["completed": .bool(true)])])])])]),
                .object(["startTime": .string("2026-08-25T13:00:00Z"), "exercises": .array([.object(["exerciseId": .string("after"), "sets": .array([.object(["completed": .bool(true)])])])])])
            ])
        ])
        XCTAssertEqual(Set(deriveTrainingState(history, asOf: "2026-08-25T12:00:00Z").objectValue!["exerciseState"]!.objectValue!.keys), Set(["before"]))
    }

  func testDatabaseLoadsAndQueries() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let db = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
    XCTAssertGreaterThan(db.count, 800)
    XCTAssertEqual(try db.getExercise("Bench_Dips").exerciseId, "Bench_Dips")
    XCTAssertFalse(db.findExercises(containing: "bench").isEmpty)
  }

  func testOffsetAwareTimestampParsingAndFutureBoundaries() throws {
    XCTAssertNotNil(parseOffsetAwareTimestamp("2026-08-25T12:00:00Z"))
    XCTAssertEqual(parseOffsetAwareTimestamp("2026-08-25T12:00:00-05:00")?.offsetSeconds, -18_000)
    XCTAssertEqual(parseOffsetAwareTimestamp("2026-08-25T12:00:00-04:00")?.offsetSeconds, -14_400)
    XCTAssertNil(parseOffsetAwareTimestamp("2026-08-25T12:00:00"))
    let history: JSONValue = .object([
      "subjectId": .string("s"), "workouts": .array([
        .object(["sessionId": .string("before"), "startTime": .string("2026-08-25T15:30:00Z"), "exercises": .array([])]),
        .object(["sessionId": .string("after"), "startTime": .string("2026-08-25T16:30:00Z"), "exercises": .array([])])
      ])
    ])
    let state = deriveTrainingState(history, asOf: "2026-08-25T12:00:00-04:00")
    XCTAssertEqual(state.objectValue?["provenance"]?.objectValue?["asOf"], .string("2026-08-25T12:00:00-04:00"))
    XCTAssertEqual(parseOffsetAwareTimestamp("2026-08-25T15:30:00Z")!.date < parseOffsetAwareTimestamp("2026-08-25T12:00:00-04:00")!.date, true)
    XCTAssertEqual(parseOffsetAwareTimestamp("2026-08-25T16:30:00Z")!.date > parseOffsetAwareTimestamp("2026-08-25T12:00:00-04:00")!.date, true)
  }

  func testOffsetAwareTimestampHandlesDSTAdjacentInstantBoundary() throws {
    let history: JSONValue = .object([
      "subjectId": .string("s"), "workouts": .array([
        .object(["sessionId": .string("before"), "startTime": .string("2026-03-08T06:00:00Z"), "exercises": .array([])]),
        .object(["sessionId": .string("after"), "startTime": .string("2026-03-08T07:00:00Z"), "exercises": .array([])])
      ])
    ])
    let state = deriveTrainingState(history, asOf: "2026-03-08T01:30:00-05:00")
    XCTAssertEqual(state.objectValue?["historyWindow"]?.objectValue?["start"], .string("2026-02-09"))
    XCTAssertEqual(parseOffsetAwareTimestamp("2026-03-08T06:00:00Z")!.date < parseOffsetAwareTimestamp("2026-03-08T01:30:00-05:00")!.date, true)
    XCTAssertEqual(parseOffsetAwareTimestamp("2026-03-08T07:00:00Z")!.date > parseOffsetAwareTimestamp("2026-03-08T01:30:00-05:00")!.date, true)
  }

  func testTypedTrainingStateContainsCompletePartMEnvelope() throws {
    let history = TrainingHistory(subjectId: "state-subject")
    let state = try TrainingEngine(database: FEDatabase(exercises: [:])).deriveTrainingState(history, asOf: "2026-08-27T12:00:00-04:00")
    XCTAssertEqual(state.stateVersion, "0.1.0")
    XCTAssertEqual(state.subjectId, "state-subject")
    XCTAssertEqual(state.asOf, "2026-08-27T12:00:00-04:00")
    XCTAssertEqual(state.historyWindow["type"], JSONValue.string("last_28_days"))
    XCTAssertEqual(state.activePlan.count, 0)
    XCTAssertEqual(state.exerciseState.count, 0)
    XCTAssertEqual(state.familyState.count, 0)
    XCTAssertEqual(state.muscleState.count, 0)
    XCTAssertEqual(state.adherenceState["sessionAdherence"], JSONValue.array([]))
    XCTAssertEqual(state.adherenceState["exercisePrescriptionAdherence"], JSONValue.array([]))
    XCTAssertEqual(state.sessionState.count, 0)
    XCTAssertEqual(state.provenance["asOf"], JSONValue.string("2026-08-27T12:00:00-04:00"))
  }

  func testTrainingStateSupportsPythonWindowModes() throws {
    let history: JSONValue = .object(["subjectId": .string("s"), "workouts": .array([
      .object(["startTime": .string("2026-08-20T12:00:00Z"), "exercises": .array([.object(["exerciseId": .string("old"), "sets": .array([])])])]),
      .object(["startTime": .string("2026-08-25T12:00:00Z"), "exercises": .array([.object(["exerciseId": .string("recent"), "sets": .array([])])])])
    ])])
    let engine = TrainingEngine(database: FEDatabase(exercises: [:]))
    let recent = engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z", window: .last7Days)
    XCTAssertEqual(recent.objectValue?["historyWindow"]?.objectValue?["type"], JSONValue.string("last_7_days"))
    XCTAssertEqual(recent.objectValue?["historyWindow"]?.objectValue?["start"], JSONValue.string("2026-08-21"))
    let custom = engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z", window: .custom(start: "2026-08-20", end: "2026-08-25"))
    XCTAssertEqual(custom.objectValue?["historyWindow"]?.objectValue?["type"], JSONValue.string("custom_date_range"))
    XCTAssertEqual(custom.objectValue?["historyWindow"]?.objectValue?["end"], JSONValue.string("2026-08-25"))
  }

  func testTrainingStateComputesCurrentCycleAndPhaseWindows() throws {
    let history: JSONValue = .object([
      "subjectId": .string("s"),
      "plans": .array([.object(["planId": .string("p"), "revisionId": .string("r"), "cycle": .object(["lengthDays": .number(7)]), "phases": .array([
        .object(["phaseId": .string("base"), "durationCycles": .number(2)]),
        .object(["phaseId": .string("build"), "durationCycles": .number(2)])
      ]), "sessions": .array([])])]),
      "planActivations": .array([.object(["planId": .string("p"), "revisionId": .string("r"), "effectiveFrom": .string("2026-08-01T00:00:00Z")])])
    ])
    let engine = TrainingEngine(database: FEDatabase(exercises: [:]))
    let cycle = engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z", window: .currentPlanCycle)
    XCTAssertEqual(cycle.objectValue?["historyWindow"]?.objectValue?["start"], JSONValue.string("2026-08-22"))
    XCTAssertEqual(cycle.objectValue?["historyWindow"]?.objectValue?["end"], JSONValue.string("2026-08-27"))
    let phase = engine.deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z", window: .currentPhase)
    XCTAssertEqual(phase.objectValue?["historyWindow"]?.objectValue?["type"], JSONValue.string("current_phase"))
    XCTAssertEqual(phase.objectValue?["historyWindow"]?.objectValue?["start"], JSONValue.string("2026-08-15"))
    XCTAssertEqual(phase.objectValue?["historyWindow"]?.objectValue?["end"], JSONValue.string("2026-08-27"))
  }

  func testActivePlanResolutionIsOrderIndependentAndHonorsReferences() throws {
    let plan1 = WorkoutPlan(schemaVersion: "0.2.0", planId: "p", revisionId: "r1", name: nil, cycle: PlanCycle(lengthDays: 7), phases: nil, sessions: [])
    let plan2 = WorkoutPlan(schemaVersion: "0.2.0", planId: "p", revisionId: "r2", name: nil, cycle: PlanCycle(lengthDays: 7), phases: nil, sessions: [])
    let history = TrainingHistory(subjectId: "s", plans: [plan2, plan1], planActivations: [
      PlanActivation(planId: "p", revisionId: "r2", effectiveFrom: "2026-08-20T00:00:00Z"),
      PlanActivation(planId: "p", revisionId: "r1", effectiveFrom: "2026-08-01T00:00:00Z", effectiveTo: "2026-08-20T00:00:00Z")
    ])
    let engine = TrainingEngine(database: FEDatabase(exercises: [:]))
    XCTAssertEqual(try engine.activePlan(in: history, asOf: "2026-08-25T12:00:00Z")?.revisionId, "r2")
    let actual = Workout(schemaVersion: "0.3.0", sessionId: "w", startTime: "2026-08-10T12:00:00Z", exercises: [], planReference: PlanReference(planId: "p", revisionId: "r1", planSessionId: nil))
    XCTAssertEqual(try engine.resolvePlan(for: actual, in: history, asOf: "2026-08-25T12:00:00Z")?.revisionId, "r1")
  }

  func testActivePlanResolutionRejectsOverlappingActivations() throws {
    let plans = [
      WorkoutPlan(schemaVersion: "0.2.0", planId: "p", revisionId: "r1", name: nil, cycle: PlanCycle(lengthDays: 7), phases: nil, sessions: []),
      WorkoutPlan(schemaVersion: "0.2.0", planId: "p", revisionId: "r2", name: nil, cycle: PlanCycle(lengthDays: 7), phases: nil, sessions: [])
    ]
    let history = TrainingHistory(subjectId: "s", plans: plans, planActivations: [
      PlanActivation(planId: "p", revisionId: "r1", effectiveFrom: "2026-08-01T00:00:00Z"),
      PlanActivation(planId: "p", revisionId: "r2", effectiveFrom: "2026-08-10T00:00:00Z")
    ])
    XCTAssertThrowsError(try TrainingEngine(database: FEDatabase(exercises: [:])).activePlan(in: history, asOf: "2026-08-15T00:00:00Z"))
  }

  func testExerciseStatePreservesPythonPerformanceFields() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let history = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/history/input.json")))
    let state = deriveTrainingState(history, asOf: "2026-08-27T12:00:00-04:00")
    let exercise = state.objectValue?["exerciseState"]?.objectValue?["Barbell_Bench_Press_-_Medium_Grip"]?.objectValue
    XCTAssertEqual(exercise?["recentSessionCount"], JSONValue.number(1))
    XCTAssertEqual(exercise?["recentCompletedSetCount"], JSONValue.number(1))
    XCTAssertEqual(exercise?["recentReps"], JSONValue.array([.number(8)]))
    XCTAssertEqual(exercise?["recentSetTypes"], JSONValue.array([.string("working")]))
    XCTAssertEqual(exercise?["latestPerformance"]?.objectValue?["sessionId"], .string("history-workout"))
    XCTAssertEqual(exercise?["lastPrescription"]?.objectValue?["prescriptionId"], .string("history-rx"))
    XCTAssertEqual(exercise?["substitutionCount"], JSONValue.number(0))
    XCTAssertEqual(exercise?["unplannedCount"], JSONValue.number(0))
    let adherence = state.objectValue?["adherenceState"]?.objectValue
    if case .array(let sessions)? = adherence?["sessionAdherence"] { XCTAssertEqual(sessions.count, 1) } else { XCTFail("missing session adherence") }
    if case .array(let rows)? = adherence?["exercisePrescriptionAdherence"], let row = rows.first?.objectValue {
      XCTAssertEqual(row["match_status"], .string("matched"))
      XCTAssertEqual(row["actual_sets"], .number(1))
    } else { XCTFail("missing exercise adherence") }
    XCTAssertEqual(adherence?["substitutionAdjustedCompletion"], .number(1))
    XCTAssertEqual(adherence?["unplannedSets"], .number(0))
  }

  func testAdherencePreservesDistinctMissingnessStates() throws {
    let history: JSONValue = .object(["subjectId": .string("s"), "plans": .array([.object(["planId": .string("p"), "revisionId": .string("r"), "cycle": .object(["lengthDays": .number(7)]), "sessions": .array([.object(["planSessionId": .string("s1"), "dayOffset": .number(0), "exercises": .array([.object(["prescriptionId": .string("rx"), "exerciseId": .string("known"), "sets": .number(1)])])])])])]), "planActivations": .array([.object(["planId": .string("p"), "revisionId": .string("r"), "effectiveFrom": .string("2026-08-01T00:00:00Z")])]), "workouts": .array([.object(["sessionId": .string("w"), "startTime": .string("2026-08-20T12:00:00Z"), "planReference": .object(["planId": .string("p"), "revisionId": .string("r"), "planSessionId": .string("s1")]), "exercises": .array([.object(["exerciseId": .string("extra"), "sets": .array([])]), .object(["exerciseId": .string("other"), "exercisePrescriptionId": .string("wrong"), "sets": .array([])])])])])])
    let state = deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z")
    guard case .array(let rows)? = state.objectValue?["adherenceState"]?.objectValue?["exercisePrescriptionAdherence"] else { return XCTFail("missing adherence rows") }
    XCTAssertTrue(rows.contains { $0.objectValue?["missingness"] == .string("not_recorded") })
    XCTAssertTrue(rows.contains { $0.objectValue?["missingness"] == .string("not_prescribed") })
    XCTAssertTrue(rows.contains { $0.objectValue?["missingness"] == .string("unable_to_match") })
  }

  func testFamilyStateUsesMembershipWithoutInferringSubstitution() throws {
    let relationships = ExerciseRelationships(schemaVersion: "1.0.0", families: ["press": ExerciseFamily(familyId: "press", name: "Press", aliases: [])], relationships: [ExerciseRelationship(sourceExerciseId: "planned", targetExerciseId: nil, familyId: "press", relationship: "member_of_family", dimensions: [:], confidence: "high"), ExerciseRelationship(sourceExerciseId: "actual", targetExerciseId: nil, familyId: "press", relationship: "member_of_family", dimensions: [:], confidence: "high")])
    let history: JSONValue = .object(["subjectId": .string("s"), "workouts": .array([.object(["sessionId": .string("w"), "startTime": .string("2026-08-20T12:00:00Z"), "exercises": .array([.object(["exerciseId": .string("actual"), "sets": .array([])])])])])])
    let state = deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z", relationships: relationships)
    let family = state.objectValue?["familyState"]?.objectValue?["press"]?.objectValue
    XCTAssertEqual(family?["recentExerciseIds"], .array([.string("actual")]))
    XCTAssertEqual(family?["mostRecentExerciseId"], .string("actual"))
    XCTAssertEqual(family?["explicitSubstitutionCount"], .number(0))
  }

  func testMuscleStateUsesDatabaseCreditsAndExposureCounts() throws {
    let exercise = Exercise(exerciseId: "x", annotation: ExerciseAnnotation(direct: ["chest"], indirect: ["triceps"], stabilizers: ["shoulders"], volumeEligible: true), source: nil)
    let database = FEDatabase(metadata: ["setCredits": .object(["direct": .number(1), "indirect": .number(0.5), "stabilizer": .number(0)])], exercises: ["x": exercise])
    let history: JSONValue = .object(["subjectId": .string("s"), "workouts": .array([.object(["sessionId": .string("w"), "startTime": .string("2026-08-20T12:00:00Z"), "exercises": .array([.object(["exerciseId": .string("x"), "sets": .array([.object(["completed": .bool(true), "setType": .string("working")])])])])])])])
    let state = deriveTrainingState(history, asOf: "2026-08-27T12:00:00Z", database: database)
    let muscles = state.objectValue?["muscleState"]?.objectValue
    XCTAssertEqual(muscles?["chest"]?.objectValue?["directSets"], .number(1))
    XCTAssertEqual(muscles?["triceps"]?.objectValue?["effectiveSets"], .number(0.5))
    XCTAssertEqual(muscles?["shoulders"]?.objectValue?["effectiveSets"], .number(0))
    XCTAssertEqual(muscles?["chest"]?.objectValue?["exposures"], .number(1))
  }

  func testProgressionMatchesCanonicalTopRepsAndEffortBoundary() throws {
    let prescription: JSONValue = .object(["prescriptionId": .string("rx"), "exerciseId": .string("x"), "load": .object(["unit": .string("kg"), "value": .number(80)]), "reps": .object(["min": .number(6), "target": .number(8), "max": .number(10)]), "sets": .number(2), "effort": .object(["rir": .object(["target": .number(2)])])])
    let state: JSONValue = .object(["planContext": .object(["planId": .string("p"), "revisionId": .string("r")]), "lastActual": .object(["sets": .array([.object(["completed": .bool(true), "reps": .number(10), "rir": .number(2)]), .object(["completed": .bool(true), "reps": .number(10), "rir": .number(2)])])])])
    let result = applyProgressionPolicy("double-progression-v1", prescription: prescription, exerciseState: state, parameters: .object(["loadIncrement": .object(["unit": .string("kg"), "value": .number(2.5)])]))
    XCTAssertEqual(result.objectValue?["decisionType"], .string("increase_load"))
    XCTAssertEqual(result.objectValue?["after"]?.objectValue?["load"]?.objectValue?["value"], .number(82.5))
    XCTAssertEqual(result.objectValue?["reasonCodes"], .array([.string("EFFORT_WITHIN_TARGET"), .string("REP_TARGET_ACHIEVED")]))
    let tooHigh = state.objectValue.map { value -> JSONValue in var copy = value; copy["lastActual"] = .object(["sets": .array([.object(["completed": .bool(true), "reps": .number(10), "rir": .number(1)]), .object(["completed": .bool(true), "reps": .number(10), "rir": .number(2)])])]); return .object(copy) } ?? .null
    XCTAssertEqual(applyProgressionPolicy("double-progression-v1", prescription: prescription, exerciseState: tooHigh).objectValue?["reasonCodes"], .array([.string("EFFORT_TOO_HIGH")]))
  }

  func testProgressionCasesMatchPythonGoldenFixture() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let input = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/progression/input.json")))
    let expected = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/progression/expected.json")))
    guard case .array(let cases)? = input.objectValue?["cases"], let parameters = input.objectValue?["parameters"] else { return XCTFail("invalid progression fixture") }
    for raw in cases {
      guard let item = raw.objectValue, case .string(let id)? = item["id"], let expectedItem = expected.objectValue?[id]?.objectValue, let prescription = item["prescription"], let state = item["state"] else { return XCTFail("invalid progression case") }
      let result = applyProgressionPolicy("double-progression-v1", prescription: prescription, exerciseState: state, parameters: parameters)
      XCTAssertEqual(result.objectValue?["decisionType"], expectedItem["decisionType"], id)
      XCTAssertEqual(result.objectValue?["reasonCodes"], expectedItem["reasonCodes"], id)
      XCTAssertEqual(result.objectValue?["after"], expectedItem["after"], id)
    }
  }

  func testTrainingEngineLoadsCanonicalBundledResources() throws {
    let engine = try TrainingEngine.bundled()
    XCTAssertGreaterThan(engine.database.count, 800)
    XCTAssertEqual(
      engine.relationships?.family(for: "Dumbbell_Bench_Press")?.familyId,
      "bench_press")
    XCTAssertNotNil(engine.database.metadata["schemaVersion"])
  }

  func testTypedCoreDomainDocumentsDecodeAndRoundTrip() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let decoder = JSONDecoder()
    let target = try decoder.decode(VolumeTarget.self, from: Data(contentsOf: root.appendingPathComponent("examples/targets/example-hypertrophy.json")))
    XCTAssertEqual(target.muscles["chest"]?.min, 8)
    let profile = try decoder.decode(TrainingProfile.self, from: Data(contentsOf: root.appendingPathComponent("examples/plan-evaluation/profile-golden.json")))
    XCTAssertEqual(profile.availability?.minutesPerSession?.max, 60)
    let plan = try decoder.decode(WorkoutPlan.self, from: Data(contentsOf: root.appendingPathComponent("examples/plans/basic-upper-lower.json")))
    let history = TrainingHistory(subjectId: "opaque", plans: [plan], targets: [target])
    let roundTrip = try decoder.decode(TrainingHistory.self, from: JSONEncoder().encode(history))
    XCTAssertEqual(roundTrip, history)
  }

  func testTypedTrainingHistoryDecodesCanonicalActualLinkage() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let decoder = JSONDecoder()
    let history = try decoder.decode(TrainingHistory.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/intent/history-aware/history.json")))
    XCTAssertEqual(history.subjectId, "fixture-subject")
    XCTAssertEqual(history.plans.first?.revisionId, "r1")
    XCTAssertEqual(history.planActivations.first?.effectiveFrom, "2026-08-01T00:00:00Z")
    XCTAssertEqual(history.workouts.first?.planReference?.planSessionId, "history-session")
    XCTAssertEqual(history.workouts.first?.exercises.first?.exercisePrescriptionId, "history-rx")
    XCTAssertEqual(history.workouts.first?.exercises.first?.sets.first?.setType, "working")
    XCTAssertEqual(history.plan(planId: "history-plan", revisionId: "r1")?.planId, "history-plan")
    XCTAssertEqual(history.activations(for: "history-plan").count, 1)
  }

  func testTypedActualSupportsSubstitutionAndUnplannedWork() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let workout = try JSONDecoder().decode(Workout.self, from: Data(contentsOf: root.appendingPathComponent("examples/workouts/plan-linked.json")))
    XCTAssertEqual(workout.exercises[1].substitution?.plannedPrescriptionId, "upper-a-row")
    XCTAssertFalse(workout.exercises[1].isUnplanned)
    let unplanned = ExerciseObservation(exerciseId: "extra", order: 3, sets: [SetObservation(setNumber: 1, setType: "working", completed: true)])
    XCTAssertTrue(unplanned.isUnplanned)
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

  func testTrainingEngineTargetFacadePreservesPartialOverrideAndConflict() {
    let engine = TrainingEngine(database: FEDatabase(exercises: [:]))
    let base: JSONValue = .object(["muscles": .object(["chest": .object(["min": .number(4), "target": .number(6), "max": .number(8)])])])
    let override: JSONValue = .object(["muscles": .object(["chest": .object(["target": .number(7)])])])
    let merged = engine.mergeTarget(base, explicit: override)
    XCTAssertEqual(merged.objectValue?["muscles"]?.objectValue?["chest"]?.objectValue?["min"], .number(4))
    XCTAssertEqual(engine.validateTarget(.object(["muscles": .object(["chest": .object(["min": .number(8), "target": .number(4)])])])), ["muscles.chest: target must not be below min"])
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

  func testWorkoutIntentHistoryAndDraftHonorCanonicalWindowAndDays() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let fixture = root.appendingPathComponent("fixtures/cross-language/intent/history-aware")
    let intent = try JSONDecoder().decode(WorkoutIntent.self, from: Data(contentsOf: fixture.appendingPathComponent("input.json")))
    let history = try JSONDecoder().decode(JSONValue.self, from: Data(contentsOf: fixture.appendingPathComponent("history.json")))
    let result = resolveIntent(intent, history: history, asOf: "2026-08-25T12:00:00Z")
    XCTAssertEqual(result.status, "resolved_with_defaults")
    XCTAssertEqual(result.generationOptions.objectValue?["trainingState"]?.objectValue?["activePlan"]?.objectValue?["revisionId"], .string("r1"))
    XCTAssertEqual(result.generationOptions.objectValue?["trainingState"]?.objectValue?["exerciseState"]?.objectValue?["Barbell_Bench_Press_-_Medium_Grip"]?.objectValue?["recentSessionCount"], .number(1))
    let database = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
    let flagship = try JSONDecoder().decode(WorkoutIntent.self, from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")))
    let generated = generatePlanFromIntent(flagship, database: database)
    let sessions: [JSONValue]
    if case .array(let values)? = generated.objectValue?["generation"]?.objectValue?["sessions"] { sessions = values } else { sessions = [] }
    XCTAssertEqual(sessions.compactMap { value in if case .number(let n)? = value.objectValue?["dayOffset"] { return Int(n) }; return nil }, [0, 1, 2, 3, 5])
  }

  func testTrainingEngineFacadeGeneratesIntentDraft() throws {
    let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath)
      .deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
    let database = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
    let intent = try JSONDecoder().decode(
      WorkoutIntent.self,
      from: Data(contentsOf: root.appendingPathComponent("fixtures/cross-language/intent/flagship-5day-hypertrophy/input.json")))
    let result = TrainingEngine(database: database).generatePlanFromIntent(intent)
    XCTAssertNotNil(result.objectValue?["resolution"])
    XCTAssertNotNil(result.objectValue?["generation"])
  }

  func testAllCanonicalResolutionFixtures() throws {
    let candidates = [
      URL(fileURLWithPath: #filePath),
      URL(fileURLWithPath: FileManager.default.currentDirectoryPath),
    ]
    let root = candidates.lazy
      .flatMap { url in sequence(first: url, next: { $0.deletingLastPathComponent() }) }
      .first { url in
        FileManager.default.fileExists(atPath: url.appendingPathComponent("free-exercise-db-plusplus.json").path)
          && FileManager.default.fileExists(atPath: url.appendingPathComponent("fixtures/cross-language/intent").path)
      }
    guard let root else { return }
    let database = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
    let decoder = JSONDecoder()
    let directories = try FileManager.default.contentsOfDirectory(at: root.appendingPathComponent("fixtures/cross-language/intent"), includingPropertiesForKeys: nil).filter { $0.hasDirectoryPath }.sorted { $0.lastPathComponent < $1.lastPathComponent }
    for directory in directories {
      // TrainingState derivation remains a v1.12 native-package item; the
      // history fixture is exercised by the Python oracle until then.
      if FileManager.default.fileExists(atPath: directory.appendingPathComponent("history.json").path) { continue }
      let intent = try decoder.decode(WorkoutIntent.self, from: Data(contentsOf: directory.appendingPathComponent("input.json")))
      let explicit = directory.appendingPathComponent("target.json")
      let target = FileManager.default.fileExists(atPath: explicit.path) ? try decoder.decode(JSONValue.self, from: Data(contentsOf: explicit)) : nil
      let result = resolveIntent(intent, database: database, target: target)
      let expected = try decoder.decode(JSONValue.self, from: Data(contentsOf: directory.appendingPathComponent("expected-resolution.json")))
      let actual = try decoder.decode(JSONValue.self, from: JSONEncoder().encode(result))
      XCTAssertEqual(actual, expected, directory.lastPathComponent)
    }
  }

}
