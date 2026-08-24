import XCTest
@testable import FreeExerciseDBPlusPlus

final class FreeExerciseDBPlusPlusTests: XCTestCase {
    func testDatabaseLoadsAndQueries() throws {
        let root = URL(fileURLWithPath: FileManager.default.currentDirectoryPath).deletingLastPathComponent().deletingLastPathComponent().deletingLastPathComponent()
        let db = try FEDatabase.load(url: root.appendingPathComponent("free-exercise-db-plusplus.json"))
        XCTAssertGreaterThan(db.count, 800)
        XCTAssertEqual(try db.getExercise("Bench_Dips").exerciseId, "Bench_Dips")
        XCTAssertFalse(db.findExercises(containing: "bench").isEmpty)
    }
    func testEffectiveSets() throws {
        let ex = Exercise(exerciseId: "x", annotation: ExerciseAnnotation(direct: ["chest"], indirect: ["triceps"], volumeEligible: true), source: nil)
        let db = FEDatabase(exercises: ["x": ex])
        let workout = Workout(schemaVersion: "0.2.0", sessionId: "s", startTime: "2026-01-01T00:00:00Z", exercises: [ExerciseObservation(exerciseId: "x", exerciseName: nil, order: 1, laterality: nil, sets: [SetObservation(setNumber: 1, setType: "working", completed: true), SetObservation(setNumber: 2, setType: "working", completed: false)])])
        XCTAssertEqual(workout.effectiveSets(using: db)["chest"], 1)
        XCTAssertEqual(workout.effectiveSets(using: db)["triceps"], 0.5)
    }
}
