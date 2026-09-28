// swift-tools-version: 6.0
import PackageDescription

// The canonical Swift package also lives under packages/swift for language-
// specific development. This root manifest makes the repository directly
// consumable by SwiftPM URL dependencies and Xcode.
let package = Package(
    name: "FreeExerciseDBPlusPlus",
    platforms: [.iOS(.v15), .macOS(.v12), .watchOS(.v8)],
    products: [
        .library(name: "FreeExerciseDBPlusPlus", targets: ["FreeExerciseDBPlusPlus"]),
        .library(name: "FreeExerciseDBPlusPlusFIT", targets: ["FreeExerciseDBPlusPlusFIT"])
    ],
    dependencies: [
        // Garmin's generated SDK is licensed separately under the FIT Protocol License.
        .package(url: "https://github.com/garmin/fit-swift-sdk.git", exact: "21.217.0")
    ],
    targets: [
        .target(
            name: "FreeExerciseDBPlusPlus",
            path: "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus",
            resources: [.process("Resources")]),
        .target(
            name: "FreeExerciseDBPlusPlusFIT",
            dependencies: ["FreeExerciseDBPlusPlus", .product(name: "FITSwiftSDK", package: "fit-swift-sdk")],
            path: "packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlusFIT"),
        .testTarget(
            name: "FreeExerciseDBPlusPlusTests",
            dependencies: ["FreeExerciseDBPlusPlus"],
            path: "packages/swift/FreeExerciseDBPlusPlus/Tests/FreeExerciseDBPlusPlusTests")
    ])
