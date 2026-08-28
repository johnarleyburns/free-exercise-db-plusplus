import Foundation
import FreeExerciseDBPlusPlus

struct ExampleFailure: Error, CustomStringConvertible {
  let description: String
}

func require(_ condition: @autoclosure () -> Bool, _ message: String) throws {
  guard condition() else { throw ExampleFailure(description: message) }
}

func requestFromBundledExample() throws -> TrainingRequest {
  guard let url = Bundle.module.url(forResource: "history-adaptation-request", withExtension: "json") else {
    throw ExampleFailure(description: "example request resource is missing")
  }
  return try JSONDecoder().decode(TrainingRequest.self, from: Data(contentsOf: url))
}

let engine = try TrainingEngine.bundled()
let persistedRequest = try requestFromBundledExample()

// A real app would load these canonical documents from persistence. This
// resource is a small standalone copy of the canonical adapt-proposal input.
guard let persistedHistory = persistedRequest.history,
      let persistedPlan = persistedRequest.currentPlan,
      let persistedProfile = persistedRequest.profile,
      let persistedTarget = persistedRequest.target,
      let asOf = persistedRequest.asOf else {
  throw ExampleFailure(description: "adaptation example resource is incomplete")
}

// These are the public Codable calls an app can use for persisted documents.
let decoder = JSONDecoder()
let history = try decoder.decode(TrainingHistory.self,
                                from: JSONEncoder().encode(persistedHistory))
let currentPlan = try decoder.decode(WorkoutPlan.self,
                                    from: JSONEncoder().encode(persistedPlan))
let profile = try decoder.decode(TrainingProfile.self,
                                 from: JSONEncoder().encode(persistedProfile))
let target = try decoder.decode(VolumeTarget.self,
                                from: JSONEncoder().encode(persistedTarget))

let stateRequest = TrainingRequest(
  requestId: "example-derive-state",
  operation: .deriveState,
  target: target,
  history: history,
  asOf: asOf,
  historyWindow: .last28Days
)
let stateResult = try engine.processTrainingRequest(stateRequest)
try require(stateResult.requestId == stateRequest.requestId, "state requestId was not preserved")
try require(stateResult.operation == .deriveState, "state operation was not preserved")

switch stateResult.status {
case "state_derived":
  guard let state = stateResult.trainingState else {
    throw ExampleFailure(description: "state_derived result has no TrainingState")
  }
  print("state: \(state.subjectId) at \(state.asOf)")

  // Progression is an optional data-driven result; no decisions is normal.
  let progressionRequest = TrainingRequest(
    requestId: "example-suggest-progression",
    operation: .suggestProgression,
    trainingState: state,
    plan: currentPlan,
    options: ["policy": .string("double-progression-v1")]
  )
  let progressionResult = try engine.processTrainingRequest(progressionRequest)
  switch progressionResult.status {
  case "progression_available":
    print("progression decisions: \(progressionResult.coachDecisions)")
  case "insufficient_data":
    print("progression: insufficient data (no decisions)")
  case "invalid", "invalid_input":
    throw ExampleFailure(description: "progression request failed: \(progressionResult.issues)")
  default:
    throw ExampleFailure(description: "unexpected progression status: \(progressionResult.status)")
  }

  let adaptationRequest = TrainingRequest(
    requestId: "example-adapt-plan",
    operation: .adaptPlan,
    profile: profile,
    target: target,
    history: history,
    currentPlan: currentPlan,
    asOf: asOf,
    options: persistedRequest.options
  )
  let adaptationResult = try engine.processTrainingRequest(adaptationRequest)
  try require(adaptationResult.requestId == adaptationRequest.requestId,
               "adaptation requestId was not preserved")
  try require(adaptationResult.operation == .adaptPlan,
               "adaptation operation was not preserved")

  switch adaptationResult.status {
  case "no_change":
    print("adaptation: no_change")
  case "revision_proposed", "regeneration_proposed":
    guard let adaptation = adaptationResult.adaptation,
          let proposedPlan = adaptation.proposedPlan else {
      throw ExampleFailure(description: "proposal result has no proposed PLAN")
    }
    let proposedPlanJSON = try JSONEncoder().encode(proposedPlan)
    print("adaptation: \(adaptationResult.status)")
    print("coach decisions: \(adaptation.decisions)")
    print("proposed PLAN bytes: \(proposedPlanJSON.count)")
    print("proposed evaluation: \(String(describing: adaptation.proposedEvaluation))")
  case "insufficient_data":
    print("adaptation: insufficient_data")
  case "invalid", "invalid_input", "unsatisfiable":
    throw ExampleFailure(description: "adaptation request failed: \(adaptationResult.issues)")
  default:
    throw ExampleFailure(description: "unexpected adaptation status: \(adaptationResult.status)")
  }
default:
  throw ExampleFailure(description: "state request failed: \(stateResult.status)")
}

print("DB++ only proposes revisions; the host app must review, persist, approve, and activate them.")
