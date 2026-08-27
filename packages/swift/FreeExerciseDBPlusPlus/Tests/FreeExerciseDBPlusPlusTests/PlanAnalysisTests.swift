import XCTest
@testable import FreeExerciseDBPlusPlus

final class PlanAnalysisTests: XCTestCase {
    func testNativePlanEvaluatorUsesDatabaseSetCreditsAndReportsTargetState() {
        let exercise = Exercise(exerciseId: "press", annotation: ExerciseAnnotation(direct: ["chest"], indirect: ["triceps"], volumeEligible: true), source: ["equipment": .string("barbell")])
        let database = FEDatabase(metadata: ["setCredits": .object(["direct": .number(1), "indirect": .number(0.25), "stabilizer": .number(0)])], exercises: ["press": exercise])
        let prescription: JSONValue = .object(["prescriptionId": .string("rx1"), "exerciseId": .string("press"), "sets": .number(4)])
        let session: JSONValue = .object(["planSessionId": .string("s1"), "dayOffset": .number(0), "exercises": .array([prescription])])
        let plan: JSONValue = .object(["schemaVersion": .string("0.2.0"), "planId": .string("p"), "revisionId": .string("r1"), "cycle": .object(["lengthDays": .number(7)]), "sessions": .array([session])])
        let profile: JSONValue = .object(["schemaVersion": .string("0.1.0"), "equipment": .array([.string("barbell")]), "availability": .object(["sessionsPerCycle": .object(["min": .number(1), "max": .number(1)]), "exercisesPerSession": .object(["min": .number(1), "max": .number(1)])])])
        let target: JSONValue = .object(["schemaVersion": .string("0.1.0"), "targetId": .string("t"), "periodDays": .number(7), "muscles": .object(["chest": .object(["min": .number(4), "target": .number(4), "max": .number(4)]), "triceps": .object(["target": .number(1)])])])
        let result = evaluatePlan(plan, database: database, profile: profile, target: target).objectValue!
        XCTAssertEqual(result["muscleCoverage"]!.objectValue!["chest"]!.objectValue!["actualEffectiveSets"], .number(4))
        XCTAssertEqual(result["muscleCoverage"]!.objectValue!["triceps"]!.objectValue!["actualEffectiveSets"], .number(1))
        XCTAssertEqual(result["summary"]!.objectValue!["evaluationStatus"], .string("valid"))
    }

    func testPlanCoverageUsesNativeCycleAndDbppCredits() {
        let exercise = Exercise(exerciseId: "x", annotation: ExerciseAnnotation(direct: ["chest"], indirect: ["triceps"], volumeEligible: true), source: nil)
        let database = FEDatabase(exercises: ["x": exercise])
        let plan = WorkoutPlan(schemaVersion: "0.1.0", planId: "p", revisionId: "r", name: "P", cycle: PlanCycle(lengthDays: 8), phases: nil, sessions: [
            PlanSession(planSessionId: "s", phaseId: nil, dayOffset: 0, exercises: [
                PlanExercisePrescription(prescriptionId: "x", exerciseId: "x", exerciseName: nil, order: 1, sets: .number(2), reps: .number(8), plannedSets: nil, progression: nil, optional: nil, condition: nil)
            ])
        ])
        let report = plan.coverage(using: database)
        XCTAssertEqual(report.nativePeriodDays, 8)
        XCTAssertEqual(report.directSets["chest"], 2)
        XCTAssertEqual(report.nativeCycle.directSetRanges["chest"], TargetRange(min: 2, target: 2, max: 2))
        XCTAssertEqual(report.effectiveSets["triceps"], 1)
        XCTAssertEqual(report.mappedSets, 2)
        XCTAssertEqual(report.coverageCompleteness.plannedSetRange, TargetRange(min: 2, target: 2, max: 2))
        XCTAssertEqual(report.unmappedSets, 0)
        XCTAssertEqual(report.normalized7Day.periodDays, 7)
        XCTAssertEqual(report.normalized7Day.directSets["chest"], 1.75)
        XCTAssertEqual(report.coverageCompleteness.mappedFraction, 1)
    }
}
