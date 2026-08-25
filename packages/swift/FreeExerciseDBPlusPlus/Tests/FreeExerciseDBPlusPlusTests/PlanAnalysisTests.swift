import XCTest
@testable import FreeExerciseDBPlusPlus

final class PlanAnalysisTests: XCTestCase {
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
        XCTAssertEqual(report.effectiveSets["triceps"], 1)
        XCTAssertEqual(report.mappedSets, 2)
        XCTAssertEqual(report.unmappedSets, 0)
        XCTAssertEqual(report.normalized7Day.periodDays, 7)
        XCTAssertEqual(report.normalized7Day.directSets["chest"], 1.75)
        XCTAssertEqual(report.coverageCompleteness.mappedFraction, 1)
    }
}
