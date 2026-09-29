import XCTest

@testable import FreeExerciseDBPlusPlus

final class HealthInteropTests: XCTestCase {
    func testHealthKitEnvelopeRoundTripsCanonicalWorkout() throws {
        let workout: JSONValue = .object([
            "schemaVersion": .string("0.3.0"),
            "sessionId": .string("session-1"),
            "startTime": .string("2026-09-29T12:00:00Z"),
            "endTime": .string("2026-09-29T12:45:00Z"),
            "exercises": .array([])
        ])
        let canonical = try JSONEncoder().encode(workout)

        let exported = try HealthInterop.export(
            workoutJSON: canonical,
            target: .healthKit)
        let envelope = try JSONDecoder().decode(HealthInteropEnvelope.self, from: exported)
        XCTAssertEqual(envelope.target, .healthKit)
        XCTAssertEqual(envelope.recordId, "session-1")
        XCTAssertEqual(envelope.canonicalWorkout, workout)

        let imported = try HealthInterop.importWorkoutJSON(exported, target: .healthKit)
        XCTAssertEqual(try JSONDecoder().decode(JSONValue.self, from: imported), workout)
    }

    func testNativeOnlyImportIsRejectedAsLossy() throws {
        let nativeOnly = Data(#"{"workoutActivityType":"traditionalStrengthTraining"}"#.utf8)

        XCTAssertThrowsError(try HealthInterop.importWorkoutJSON(
            nativeOnly,
            target: .healthKit,
            mode: .allowLossy)) { error in
            guard case HealthInteropError.lossyImport(let losses) = error else {
                return XCTFail("expected a structured lossy-import error")
            }
            XCTAssertEqual(losses.first?.path, "canonicalWorkout")
        }
    }
}
