// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "FreeExerciseDBPlusPlus",
    platforms: [.iOS(.v15), .macOS(.v12), .watchOS(.v8)],
    products: [.library(name: "FreeExerciseDBPlusPlus", targets: ["FreeExerciseDBPlusPlus"])],
    targets: [
        .target(name: "FreeExerciseDBPlusPlus", resources: [.process("Resources")]),
        .testTarget(name: "FreeExerciseDBPlusPlusTests", dependencies: ["FreeExerciseDBPlusPlus"])
    ]
)
