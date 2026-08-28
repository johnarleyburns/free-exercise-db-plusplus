// swift-tools-version: 6.0
import PackageDescription

// The canonical Swift package also lives under packages/swift for language-
// specific development. This root manifest makes the repository directly
// consumable by SwiftPM URL dependencies and Xcode.
let package = Package(
    name: "FreeExerciseDBPlusPlus",
    platforms: [.iOS(.v15), .macOS(.v12), .watchOS(.v8)],
    products: [.library(name: "FreeExerciseDBPlusPlus", targets: ["FreeExerciseDBPlusPlus"])],
    targets: [
        .target(
            name: "FreeExerciseDBPlusPlus",
            path: "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus",
            resources: [.process("Resources")]),
        .testTarget(
            name: "FreeExerciseDBPlusPlusTests",
            dependencies: ["FreeExerciseDBPlusPlus"],
            path: "packages/swift/FreeExerciseDBPlusPlus/Tests/FreeExerciseDBPlusPlusTests")
    ])
