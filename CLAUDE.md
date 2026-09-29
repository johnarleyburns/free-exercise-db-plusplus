# Project Session Workflow

Work on one roadmap phase at a time. A phase must be scoped so it can reasonably be completed in one session.

At the start of every session:

1. Read `current_status.md` first. Treat it as the local handoff for the current project state, recent work, future work, and the active phase.
2. Read the roadmap and any project files referenced by `current_status.md` that are relevant to the active phase.
3. Implement only the active phase. Preserve the v1.0 exercise-database consumer contract and follow the guardrails in `ROADMAP.md`.

Before finishing a phase:

1. Re-read the phase plan and audit the implementation for completeness and correctness.
2. Run the full relevant unit-test suite, not only newly added tests.
3. Add or update integration/CI validation when the phase changes behavior covered by those checks.
4. Review the final diff and working tree, preserving unrelated user changes.
5. Commit and push the completed implementation only after the audit and tests pass.
6. After the push, update `current_status.md` with the completed work, verification results, important decisions, remaining risks, and the next active phase.

`current_status.md` is a local working handoff file. Never stage, commit, or push it. Check the staged file list before every commit to enforce this rule.

## Swift and iOS validation

Run the package's host-side tests with:

```sh
swift test --package-path packages/swift/FreeExerciseDBPlusPlus
```

Do not use `swift build --sdk "$(xcrun --sdk iphoneos --show-sdk-path)" --triple arm64-apple-ios15.0` as the iOS validation command. SwiftPM compiles `Package.swift` for the host before compiling package targets; combining the host manifest target with the iPhoneOS SDK produces the misleading `using sysroot for 'iPhoneOS' but targeting 'MacOSX'` / `unable to load standard library` failure.

For a direct iOS target check, first let SwiftPM generate its resource accessor in an isolated scratch directory. Keep the host SDK on the manifest invocation and pass the iPhoneOS SDK to the target compiler; this avoids contaminating the normal host-test build directory:

```sh
IOS_SDK="$(xcrun --sdk iphoneos --show-sdk-path)"
MAC_SDK="$(xcrun --sdk macosx --show-sdk-path)"
IOS_SCRATCH="$(mktemp -d "${TMPDIR:-/tmp}/fedbpp-ios-build.XXXXXX")"
swift build \
  --package-path packages/swift/FreeExerciseDBPlusPlus \
  --scratch-path "$IOS_SCRATCH" \
  --sdk "$MAC_SDK" \
  --triple arm64-apple-ios15.0 \
  -Xswiftc -sdk -Xswiftc "$IOS_SDK" \
  -Xlinker -sdk -Xlinker "$IOS_SDK"
SWIFT_SOURCES=(packages/swift/FreeExerciseDBPlusPlus/Sources/FreeExerciseDBPlusPlus/*.swift)
RESOURCE_ACCESSOR="$IOS_SCRATCH/arm64-apple-ios/debug/FreeExerciseDBPlusPlus.build/DerivedSources/resource_bundle_accessor.swift"
xcrun --sdk iphoneos swiftc \
  -typecheck -parse-as-library \
  -target arm64-apple-ios15.0 -sdk "$IOS_SDK" \
  -module-name FreeExerciseDBPlusPlus \
  "$RESOURCE_ACCESSOR" "${SWIFT_SOURCES[@]}"
```

The authoritative consumer validation is an Xcode build of the iOS app or framework that consumes this package, using `xcodebuild -sdk iphoneos` or an iOS device destination. A generic device build may still stop at app signing or provisioning; report that separately from compiler or SDK failures.
