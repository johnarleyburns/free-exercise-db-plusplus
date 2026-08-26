import Foundation

public enum FEDBError: Error, LocalizedError, Sendable {
    case invalidDocument(String)
    case exerciseNotFound(String)
    public var errorDescription: String? {
        switch self { case .invalidDocument(let message): return message; case .exerciseNotFound(let id): return "Exercise not found: \(id)" }
    }
}

public indirect enum JSONValue: Codable, Sendable, Equatable {
    case null, bool(Bool), number(Double), string(String), array([JSONValue]), object([String: JSONValue])
    public init(from decoder: Decoder) throws {
        let c = try decoder.singleValueContainer()
        if c.decodeNil() { self = .null }
        else if let v = try? c.decode(Bool.self) { self = .bool(v) }
        else if let v = try? c.decode(Double.self) { self = .number(v) }
        else if let v = try? c.decode(String.self) { self = .string(v) }
        else if let v = try? c.decode([JSONValue].self) { self = .array(v) }
        else { self = .object(try c.decode([String: JSONValue].self)) }
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.singleValueContainer()
        switch self { case .null: try c.encodeNil(); case .bool(let v): try c.encode(v); case .number(let v): try c.encode(v); case .string(let v): try c.encode(v); case .array(let v): try c.encode(v); case .object(let v): try c.encode(v) }
    }
}
public extension JSONValue {
    var objectValue: [String: JSONValue]? { if case .object(let value) = self { return value }; return nil }
}

public struct ExerciseAnnotation: Codable, Sendable, Equatable {
    public let direct: [String]
    public let indirect: [String]
    public let stabilizers: [String]
    public var patterns: [String] = []
    public let volumeEligible: Bool
    public let confidence: String?
    public init(direct: [String] = [], indirect: [String] = [], stabilizers: [String] = [], volumeEligible: Bool = false, confidence: String? = nil) { self.direct = direct; self.indirect = indirect; self.stabilizers = stabilizers; self.patterns = []; self.volumeEligible = volumeEligible; self.confidence = confidence }
}

public struct Exercise: Codable, Sendable, Equatable, Identifiable {
    public let exerciseId: String
    public let annotation: ExerciseAnnotation
    public let source: [String: JSONValue]?
    public var id: String { exerciseId }
}

private struct DatabaseDocument: Codable, Sendable { let metadata: [String: JSONValue]?; let exercises: [String: Exercise] }

public struct FEDatabase: Sendable {
    public let metadata: [String: JSONValue]
    private let exercises: [String: Exercise]
    public static func load(url: URL) throws -> FEDatabase {
        let data = try Data(contentsOf: url)
        do { let doc = try JSONDecoder().decode(DatabaseDocument.self, from: data); return FEDatabase(metadata: doc.metadata ?? [:], exercises: doc.exercises) }
        catch { throw FEDBError.invalidDocument("Unable to decode database: \(error)") }
    }
    public init(metadata: [String: JSONValue] = [:], exercises: [String: Exercise]) { self.metadata = metadata; self.exercises = exercises }
    public var count: Int { exercises.count }
    public var exerciseIDs: Set<String> { Set(exercises.keys) }
    public var setCredits: (direct: Double, indirect: Double, stabilizer: Double) {
        guard case .object(let values)? = metadata["setCredits"] else { return (1, 0.5, 0) }
        func number(_ key: String, _ fallback: Double) -> Double { if case .number(let value)? = values[key] { return value }; return fallback }
        return (number("direct", 1), number("indirect", 0.5), number("stabilizer", 0))
    }
    public func getExercise(_ id: String) throws -> Exercise { guard let e = exercises[id] else { throw FEDBError.exerciseNotFound(id) }; return e }
    public func findExercises(containing query: String) -> [Exercise] { let q = query.lowercased(); return exercises.values.filter { $0.exerciseId.lowercased().contains(q) }.sorted { $0.exerciseId < $1.exerciseId } }
    public func exercisesForMuscle(_ muscle: String) -> [Exercise] { exercises.values.filter { $0.annotation.direct.contains(muscle) || $0.annotation.indirect.contains(muscle) }.sorted { $0.exerciseId < $1.exerciseId } }
    public var equipmentVocabulary: Set<String> { Set(exercises.values.compactMap { if case .string(let value)? = $0.source?["equipment"] { return value }; return nil }) }
}

public struct Quantity: Codable, Sendable, Equatable { public let value: Double; public let unit: String }
public struct SetObservation: Codable, Sendable, Equatable { public let setNumber: Int; public let setType: String; public let reps: Int?; public let load: Quantity?; public let completed: Bool; public let resistance: [String: JSONValue]?; public init(setNumber: Int, setType: String, reps: Int? = nil, load: Quantity? = nil, completed: Bool) { self.setNumber = setNumber; self.setType = setType; self.reps = reps; self.load = load; self.completed = completed; self.resistance = nil } }
public struct ExerciseObservation: Codable, Sendable, Equatable { public let exerciseId: String?; public let exerciseName: String?; public let order: Int; public let laterality: String?; public let sets: [SetObservation] }
public struct Workout: Codable, Sendable, Equatable {
    public let schemaVersion: String; public let sessionId: String; public let startTime: String; public let endTime: String?; public let exercises: [ExerciseObservation]
    public init(schemaVersion: String, sessionId: String, startTime: String, endTime: String? = nil, exercises: [ExerciseObservation]) { self.schemaVersion = schemaVersion; self.sessionId = sessionId; self.startTime = startTime; self.endTime = endTime; self.exercises = exercises }
    public static func load(url: URL, decoder: JSONDecoder = JSONDecoder()) throws -> Workout { do { return try decoder.decode(Workout.self, from: Data(contentsOf: url)) } catch { throw FEDBError.invalidDocument("Unable to decode workout: \(error)") } }
    public func effectiveSets(using database: FEDatabase) -> [String: Double] { var totals: [String: Double] = [:]; for observation in exercises { guard let id = observation.exerciseId, let exercise = try? database.getExercise(id), exercise.annotation.volumeEligible else { continue }; let credits = database.setCredits; let counted = Set(["working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"]); let sets = Double(observation.sets.filter { $0.completed && counted.contains($0.setType) }.count); for muscle in exercise.annotation.direct { totals[muscle, default: 0] += sets * credits.direct }; for muscle in exercise.annotation.indirect { totals[muscle, default: 0] += sets * credits.indirect }; for muscle in exercise.annotation.stabilizers { totals[muscle, default: 0] += sets * credits.stabilizer } }; return totals }
}

public struct PlanCycle: Codable, Sendable, Equatable { public let lengthDays: Int }
public struct PlanPhase: Codable, Sendable, Equatable { public let phaseId: String; public let durationCycles: Int; public let cycle: PlanCycle? }
public struct PlannedSet: Codable, Sendable, Equatable { public let setPrescriptionId: String; public let setType: String; public let reps: JSONValue; public let load: JSONValue?; public var effort: JSONValue? = nil; public var notes: String? = nil }
public struct PlanExercisePrescription: Codable, Sendable, Equatable { public let prescriptionId: String; public let exerciseId: String?; public let exerciseName: String?; public var externalExerciseId: JSONValue? = nil; public let order: Int; public let sets: JSONValue?; public let reps: JSONValue?; public var load: JSONValue? = nil; public var effort: JSONValue? = nil; public var setType: String? = nil; public var laterality: String? = nil; public var notes: String? = nil; public let plannedSets: [PlannedSet]?; public let progression: JSONValue?; public let optional: Bool?; public let condition: String? }
public struct PlanSession: Codable, Sendable, Equatable { public let planSessionId: String; public let phaseId: String?; public let dayOffset: Int; public var name: String? = nil; public var notes: String? = nil; public let exercises: [PlanExercisePrescription] }
public struct WorkoutPlan: Codable, Sendable, Equatable {
    public let schemaVersion: String; public let planId: String; public let revisionId: String; public let name: String; public var description: String? = nil; public var provenance: JSONValue? = nil; public let cycle: PlanCycle; public var notes: String? = nil; public var tags: [String]? = nil; public let phases: [PlanPhase]?; public let sessions: [PlanSession]
    public static func load(url: URL, decoder: JSONDecoder = JSONDecoder()) throws -> WorkoutPlan { do { return try decoder.decode(WorkoutPlan.self, from: Data(contentsOf: url)) } catch { throw FEDBError.invalidDocument("Unable to decode PLAN: \(error)") } }
}

public struct ExerciseFamily: Codable, Sendable, Equatable { public let familyId: String; public let name: String; public let aliases: [String] }
public struct ExerciseRelationship: Codable, Sendable, Equatable { public let sourceExerciseId: String; public let targetExerciseId: String?; public let familyId: String; public let relationship: String; public let dimensions: [String: JSONValue]; public let confidence: String }
public struct ExerciseRelationships: Codable, Sendable, Equatable {
    public let schemaVersion: String; public let families: [String: ExerciseFamily]; public let relationships: [ExerciseRelationship]
    public static func load(url: URL, decoder: JSONDecoder = JSONDecoder()) throws -> ExerciseRelationships { do { return try decoder.decode(ExerciseRelationships.self, from: Data(contentsOf: url)) } catch { throw FEDBError.invalidDocument("Unable to decode relationships: \(error)") } }
    public func family(for exerciseId: String) -> ExerciseFamily? { guard let row = relationships.first(where: { $0.sourceExerciseId == exerciseId && $0.relationship == "member_of_family" }) else { return nil }; return families[row.familyId] }
    public func members(of familyId: String) -> [String] { relationships.filter { $0.familyId == familyId && $0.relationship == "member_of_family" }.map(\.sourceExerciseId).sorted() }
}
