import Foundation

public enum HealthInteropTarget: String, Codable, Sendable {
    case garminFIT = "garmin-fit"
    case healthKit = "healthkit"
    case healthConnect = "health-connect"
}

public enum HealthInteropMode: String, Codable, Sendable {
    case strict
    case allowLossy = "allow-lossy"
}

public struct HealthInteropLoss: Codable, Sendable, Equatable {
    public let path: String
    public let reason: String
    public let destination: String
    public init(path: String, reason: String, destination: String) {
        self.path = path; self.reason = reason; self.destination = destination
    }
}

public struct HealthInteropEnvelope: Codable, Sendable, Equatable {
    public let interopVersion: String
    public let target: HealthInteropTarget
    public let recordId: String
    public let canonicalWorkout: JSONValue?
    public let projection: JSONValue
    public let fidelity: String
    public let losses: [HealthInteropLoss]
    public let warnings: [String]

    public init(interopVersion: String = "0.1.0", target: HealthInteropTarget, recordId: String,
                canonicalWorkout: JSONValue?, projection: JSONValue, fidelity: String = "lossless_with_sidecar",
                losses: [HealthInteropLoss] = [], warnings: [String] = []) {
        self.interopVersion = interopVersion; self.target = target; self.recordId = recordId
        self.canonicalWorkout = canonicalWorkout; self.projection = projection; self.fidelity = fidelity
        self.losses = losses; self.warnings = warnings
    }
}

public enum HealthInteropError: Error, LocalizedError, Sendable {
    case invalidWorkout(String)
    case invalidEnvelope(String)
    case lossyImport([HealthInteropLoss])
    case platformUnavailable(String)

    public var errorDescription: String? {
        switch self {
        case .invalidWorkout(let message): return message
        case .invalidEnvelope(let message): return message
        case .lossyImport(let losses): return "Health import is lossy: \(losses.map(\.reason).joined(separator: "; "))"
        case .platformUnavailable(let message): return message
        }
    }
}

/// Platform-neutral contract shared by FIT, HealthKit, and Health Connect
/// bindings. Native records are projections; `canonicalWorkout` is the
/// sidecar that preserves every DB++ field during a round trip.
public enum HealthInterop {
    public static let version = "0.1.0"
    public static let canonicalMetadataKey = "org.free-exercise-db-plusplus.canonicalWorkoutJSON"

    public static func export(workoutJSON: Data, target: HealthInteropTarget, mode: HealthInteropMode = .strict) throws -> Data {
        let workout = try canonicalWorkout(from: workoutJSON)
        guard let values = workout.objectValue,
              case .string(let sessionId)? = values["sessionId"],
              case .string(let startTime)? = values["startTime"] else {
            throw HealthInteropError.invalidWorkout("DB++ ACTUAL requires sessionId and startTime")
        }
        let canonical = try canonicalJSONString(workoutJSON)
        let projection = makeProjection(workout: values, target: target, canonicalJSON: canonical, startTime: startTime)
        let envelope = HealthInteropEnvelope(target: target, recordId: sessionId, canonicalWorkout: workout,
                                             projection: projection,
                                             warnings: ["Persist the canonical sidecar with the native record; target APIs do not represent every DB++ field."])
        return try JSONEncoder().encode(envelope)
    }

    public static func importWorkoutJSON(_ externalJSON: Data, target: HealthInteropTarget,
                                         mode: HealthInteropMode = .strict) throws -> Data {
        let value = try decodeJSON(externalJSON)
        if let canonical = canonicalFrom(value) {
            return try encode(canonical)
        }
        let losses = [HealthInteropLoss(path: "canonicalWorkout", reason: "native record has no DB++ sidecar", destination: "full DB++ ACTUAL")]
        if mode == .strict { throw HealthInteropError.lossyImport(losses) }
        throw HealthInteropError.lossyImport(losses)
    }

    public static func canonicalWorkout(from data: Data) throws -> JSONValue {
        let value = try decodeJSON(data)
        guard let object = value.objectValue,
              case .string(let version)? = object["schemaVersion"], ["0.2.0", "0.3.0"].contains(version),
              case .array? = object["exercises"] else {
            throw HealthInteropError.invalidWorkout("unsupported or malformed DB++ ACTUAL JSON")
        }
        return value
    }

    public static func decodeJSON(_ data: Data) throws -> JSONValue {
        do { return try JSONDecoder().decode(JSONValue.self, from: data) }
        catch { throw HealthInteropError.invalidEnvelope("invalid JSON: \(error)") }
    }

    public static func encode(_ value: JSONValue) throws -> Data {
        try JSONEncoder().encode(value)
    }

    private static func canonicalJSONString(_ data: Data) throws -> String {
        guard let value = String(data: data, encoding: .utf8) else {
            throw HealthInteropError.invalidWorkout("canonical workout must be UTF-8 JSON")
        }
        return value
    }

    private static func makeProjection(workout: [String: JSONValue], target: HealthInteropTarget,
                                       canonicalJSON: String, startTime: String) -> JSONValue {
        let endTime = workout["endTime"] ?? .null
        switch target {
        case .garminFIT:
            return .object([
                "fileType": .string("activity"),
                "fileId": .object(["type": .string("activity"), "timeCreated": .string(startTime)]),
                "session": .object(["startTime": .string(startTime), "endTime": endTime, "sport": .string("strength_training")]),
                "developerData": .object(["namespace": .string("org.free-exercise-db-plusplus"), "canonicalWorkoutJSON": .string(canonicalJSON)])
            ])
        case .healthKit:
            return .object([
                "workoutActivityType": .string("traditionalStrengthTraining"),
                "startDate": .string(startTime), "endDate": endTime,
                "metadata": .object(["org.free-exercise-db-plusplus.sessionId": workout["sessionId"] ?? .null,
                                      canonicalMetadataKey: .string(canonicalJSON)])
            ])
        case .healthConnect:
            return .object([
                "startTime": .string(startTime), "endTime": endTime,
                "exerciseType": .string("strength_training"),
                "metadata": .object(["clientRecordId": workout["sessionId"] ?? .null,
                                      canonicalMetadataKey: .string(canonicalJSON)])
            ])
        }
    }

    private static func canonicalFrom(_ value: JSONValue) -> JSONValue? {
        guard let root = value.objectValue else { return nil }
        if let canonical = root["canonicalWorkout"], canonical.objectValue != nil { return canonical }
        guard let projection = root["projection"]?.objectValue else { return nil }
        for container in [projection, projection["metadata"]?.objectValue, projection["developerData"]?.objectValue].compactMap({ $0 }) {
            if case .string(let raw)? = container[canonicalMetadataKey] ?? container["canonicalWorkoutJSON"],
               let data = raw.data(using: .utf8), let parsed = try? decodeJSON(data) { return parsed }
        }
        return nil
    }
}

#if canImport(HealthKit)
import HealthKit

/// Real HealthKit bridge. It saves the DB++ JSON in metadata and writes the
/// standard session summary as an HKWorkout. Apps must still request the
/// HealthKit entitlement and user authorization themselves.
@available(iOS 15.0, macOS 13.0, watchOS 8.0, *)
public final class HealthKitAdapter: @unchecked Sendable {
    public let store: HKHealthStore

    public init(store: HKHealthStore = HKHealthStore()) { self.store = store }

    public func requestAuthorization() async throws {
        let workoutType = HKObjectType.workoutType()
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            store.requestAuthorization(toShare: [workoutType], read: [workoutType]) { success, error in
                if let error { continuation.resume(throwing: error) }
                else if success { continuation.resume() }
                else { continuation.resume(throwing: HealthInteropError.platformUnavailable("HealthKit authorization was not granted")) }
            }
        }
    }

    public func export(workoutJSON: Data) async throws -> HKWorkout {
        let value = try HealthInterop.canonicalWorkout(from: workoutJSON)
        guard let fields = value.objectValue,
              case .string(let startText)? = fields["startTime"],
              let start = ISO8601DateFormatter().date(from: startText) else {
            throw HealthInteropError.invalidWorkout("startTime must be an ISO-8601 timestamp")
        }
        let endDate: Date = if case .string(let text)? = fields["endTime"], let parsed = ISO8601DateFormatter().date(from: text) { parsed } else { start }
        let configuration = HKWorkoutConfiguration()
        configuration.activityType = .traditionalStrengthTraining
        let builder = HKWorkoutBuilder(healthStore: store, configuration: configuration, device: nil)
        try await begin(builder, start: start)
        let canonical = String(data: workoutJSON, encoding: .utf8) ?? ""
        try await addMetadata(builder, metadata: [HealthInterop.canonicalMetadataKey: canonical,
                                                  "org.free-exercise-db-plusplus.sessionId": (fields["sessionId"]?.stringValue ?? "")])
        try await end(builder, end: endDate)
        return try await finish(builder)
    }

    public func importCanonicalWorkouts() async throws -> [Data] {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<[Data], Error>) in
            let query = HKSampleQuery(sampleType: HKObjectType.workoutType(), predicate: nil,
                                      limit: HKObjectQueryNoLimit, sortDescriptors: nil) { _, samples, error in
                if let error { continuation.resume(throwing: error); return }
                let data = (samples as? [HKWorkout] ?? []).compactMap { workout in
                    (workout.metadata?[HealthInterop.canonicalMetadataKey] as? String)?.data(using: .utf8)
                }
                continuation.resume(returning: data)
            }
            store.execute(query)
        }
    }

    private func begin(_ builder: HKWorkoutBuilder, start: Date) async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            builder.beginCollection(withStart: start) { success, error in
                if let error { continuation.resume(throwing: error) }
                else if success { continuation.resume() }
                else { continuation.resume(throwing: HealthInteropError.platformUnavailable("HealthKit could not begin collection")) }
            }
        }
    }

    private func addMetadata(_ builder: HKWorkoutBuilder, metadata: [String: Any]) async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            builder.addMetadata(metadata) { success, error in
                if let error { continuation.resume(throwing: error) }
                else if success { continuation.resume() }
                else { continuation.resume(throwing: HealthInteropError.platformUnavailable("HealthKit could not save metadata")) }
            }
        }
    }

    private func end(_ builder: HKWorkoutBuilder, end: Date) async throws {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<Void, Error>) in
            builder.endCollection(withEnd: end) { success, error in
                if let error { continuation.resume(throwing: error) }
                else if success { continuation.resume() }
                else { continuation.resume(throwing: HealthInteropError.platformUnavailable("HealthKit could not end collection")) }
            }
        }
    }

    private func finish(_ builder: HKWorkoutBuilder) async throws -> HKWorkout {
        try await withCheckedThrowingContinuation { (continuation: CheckedContinuation<HKWorkout, Error>) in
            builder.finishWorkout { workout, error in
                if let error { continuation.resume(throwing: error) }
                else if let workout { continuation.resume(returning: workout) }
                else { continuation.resume(throwing: HealthInteropError.platformUnavailable("HealthKit did not return a workout")) }
            }
        }
    }
}

private extension JSONValue {
    var stringValue: String? { if case .string(let value) = self { return value }; return nil }
}
#endif
