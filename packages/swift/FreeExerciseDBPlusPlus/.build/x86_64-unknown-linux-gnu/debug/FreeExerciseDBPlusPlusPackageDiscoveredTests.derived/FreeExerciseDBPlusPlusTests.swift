import XCTest
@testable import FreeExerciseDBPlusPlusTests

fileprivate extension FreeExerciseDBPlusPlusTests {
    @available(*, deprecated, message: "Not actually deprecated. Marked as deprecated to allow inclusion of deprecated tests (which test deprecated functionality) without warnings")
    static nonisolated(unsafe) let __allTests__FreeExerciseDBPlusPlusTests = [
        ("testDatabaseLoadsAndQueries", testDatabaseLoadsAndQueries),
        ("testEffectiveSets", testEffectiveSets)
    ]
}
@available(*, deprecated, message: "Not actually deprecated. Marked as deprecated to allow inclusion of deprecated tests (which test deprecated functionality) without warnings")
func __FreeExerciseDBPlusPlusTests__allTests() -> [XCTestCaseEntry] {
    return [
        testCase(FreeExerciseDBPlusPlusTests.__allTests__FreeExerciseDBPlusPlusTests)
    ]
}