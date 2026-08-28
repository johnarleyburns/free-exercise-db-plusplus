// swift-tools-version: 6.0
import PackageDescription

let package = Package(
  name: "FEDBPPApplicationExample",
  platforms: [.iOS(.v15), .macOS(.v12), .watchOS(.v8)],
  dependencies: [.package(path: "../../../packages/swift/FreeExerciseDBPlusPlus")],
  targets: [.executableTarget(name: "AppIntegration",
                              dependencies: [.product(name: "FreeExerciseDBPlusPlus",
                                                      package: "FreeExerciseDBPlusPlus")])]
)
