# ADR 0027: Swift native engine architecture

Status: accepted (v1.11)

The v1.11 native engine is implemented in the existing
`packages/swift/FreeExerciseDBPlusPlus` Swift package. The package remains a
Foundation-only library and is suitable for offline application use on the
platforms declared by its manifest.

## Decisions

- Swift 6 is the package language mode.
- Foundation supplies Codable, URL/resource loading, dates, and value
  utilities; no UI framework is required.
- Portable domain values are immutable structs or enums and conform to
  `Codable`, `Equatable`, and `Sendable` where appropriate.
- `JSONValue` is retained as an internal/forward-compatible representation for
  evolving document fields during the migration. It is not permission to add
  an external runtime or a second package.
- Database and relationship artifacts are injected into the engine as values;
  resource loading and application-facing façade additions remain within this
  package.
- The engine has no network calls, subprocesses, Python bridge, LLM, global
  mutable state, SwiftUI, UIKit, or AppKit dependency.

This ADR establishes the implementation boundary for the remaining Swift
engine parts. It does not claim evaluator, generator, history, progression, or
adaptive parity; those capabilities are implemented and verified in their
ordered follow-on phases.
