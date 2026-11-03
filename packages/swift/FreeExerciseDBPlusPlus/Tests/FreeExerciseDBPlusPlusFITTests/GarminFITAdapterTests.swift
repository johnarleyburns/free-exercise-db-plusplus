import Foundation
import XCTest
@testable import FreeExerciseDBPlusPlusFIT

final class GarminFITAdapterTests: XCTestCase {
    private let adapter = GarminFITAdapter()

    private func workout() throws -> Data {
        try JSONSerialization.data(withJSONObject: [
            "schemaVersion": "0.3.0",
            "sessionId": "fit-unit-test",
            "startTime": "2026-11-02T18:30:00Z",
            "endTime": "2026-11-02T19:15:00Z",
            "exercises": [[
                "exerciseId": "Barbell_Bench_Press", "order": 1,
                "sets": [["setNumber": 1, "setType": "working", "reps": 8,
                          "load": ["value": 100, "unit": "kg"], "completed": true,
                          "notes": "Unicode must survive: café 💪"]
            ]]]
        ], options: [.sortedKeys])
    }

    func testBinaryRoundTripPreservesCanonicalActual() throws {
        let source = try workout()
        let fit = try adapter.exportActivity(workoutJSON: source)
        XCTAssertGreaterThan(fit.count, 14)
        XCTAssertEqual(try adapter.importActivity(fit), source)
    }

    func testRejectsNonFITInput() {
        XCTAssertThrowsError(try adapter.importActivity(Data("not a FIT file".utf8)))
    }
}
