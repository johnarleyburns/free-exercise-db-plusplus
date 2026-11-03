// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "FreeExerciseDBPlusPlus",
    platforms: [.iOS(.v15), .macOS(.v12), .watchOS(.v8)],
    products: [
        .library(name: "FreeExerciseDBPlusPlus", targets: ["FreeExerciseDBPlusPlus"]),
        .library(name: "FreeExerciseDBPlusPlusFIT", targets: ["FreeExerciseDBPlusPlusFIT"])
    ],
    dependencies: [
        // Garmin's generated SDK is separately licensed under the FIT Protocol License.
        .package(url: "https://github.com/garmin/fit-swift-sdk.git", exact: "21.217.0")
    ],
    targets: [
        .target(name: "FreeExerciseDBPlusPlus", resources: [.process("Resources")]),
        .target(
            name: "FreeExerciseDBPlusPlusFIT",
            dependencies: ["FreeExerciseDBPlusPlus", .product(name: "FITSwiftSDK", package: "fit-swift-sdk")]),
        .testTarget(name: "FreeExerciseDBPlusPlusTests", dependencies: ["FreeExerciseDBPlusPlus"]),
        .testTarget(name: "FreeExerciseDBPlusPlusFITTests", dependencies: ["FreeExerciseDBPlusPlusFIT"])
    ]
)
