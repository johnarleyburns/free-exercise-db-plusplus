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
        switch self {
        case .object(let v):
            // JSON object order is not semantic, but sorted keys make persisted
            // app artifacts byte-stable across processes and Swift runtimes.
            var keyed = encoder.container(keyedBy: JSONValueCodingKey.self)
            for key in v.keys.sorted() {
                try keyed.encode(v[key], forKey: JSONValueCodingKey(stringValue: key))
            }
        case .null:
            var c = encoder.singleValueContainer(); try c.encodeNil()
        case .bool(let v):
            var c = encoder.singleValueContainer(); try c.encode(v)
        case .number(let v):
            var c = encoder.singleValueContainer(); try c.encode(v)
        case .string(let v):
            var c = encoder.singleValueContainer(); try c.encode(v)
        case .array(let v):
            var c = encoder.singleValueContainer(); try c.encode(v)
        }
    }
}

private struct JSONValueCodingKey: CodingKey {
    let stringValue: String
    let intValue: Int? = nil
    init(stringValue: String) { self.stringValue = stringValue }
    init?(intValue: Int) { return nil }
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
    public init(exerciseId: String, annotation: ExerciseAnnotation, source: [String: JSONValue]? = nil) {
        self.exerciseId = exerciseId; self.annotation = annotation; self.source = source
    }
    public var id: String { exerciseId }
}

private struct DatabaseDocument: Codable, Sendable { let metadata: [String: JSONValue]?; let exercises: [String: Exercise] }

public struct FEDatabase: Sendable {
    public let metadata: [String: JSONValue]
    private let exercises: [String: Exercise]
    private let indexes: DatabaseIndexes
    public static func load(url: URL) throws -> FEDatabase {
        let data = try Data(contentsOf: url)
        do { let doc = try JSONDecoder().decode(DatabaseDocument.self, from: data); return FEDatabase(metadata: doc.metadata ?? [:], exercises: doc.exercises) }
        catch { throw FEDBError.invalidDocument("Unable to decode database: \(error)") }
    }
    public init(metadata: [String: JSONValue] = [:], exercises: [String: Exercise]) {
        self.metadata = metadata
        self.exercises = exercises
        self.indexes = DatabaseIndexes(exercises: exercises)
    }
    public var count: Int { exercises.count }
    public var exerciseIDs: Set<String> { Set(exercises.keys) }
    /// Stable DB++ exercise view for native analysis and planning.
    public var allExercises: [String: Exercise] { exercises }
    public var setCredits: (direct: Double, indirect: Double, stabilizer: Double) {
        guard case .object(let values)? = metadata["setCredits"] else { return (1, 0.5, 0) }
        func number(_ key: String, _ fallback: Double) -> Double { if case .number(let value)? = values[key] { return value }; return fallback }
        return (number("direct", 1), number("indirect", 0.5), number("stabilizer", 0))
    }
    public func getExercise(_ id: String) throws -> Exercise { guard let e = exercises[id] else { throw FEDBError.exerciseNotFound(id) }; return e }
    public func findExercises(containing query: String) -> [Exercise] { let q = query.lowercased(); return indexes.all.filter { $0.exerciseId.lowercased().contains(q) } }
    public func exercisesForMuscle(_ muscle: String) -> [Exercise] { indexes.byMuscle[muscle, default: []].compactMap { exercises[$0] } }
    public func exercisesForMovementPattern(_ pattern: String) -> [Exercise] { indexes.byMovementPattern[pattern, default: []].compactMap { exercises[$0] } }
    public func exercisesForEquipment(_ equipment: String) -> [Exercise] { indexes.byEquipment[equipment, default: []].compactMap { exercises[$0] } }
    public var equipmentVocabulary: Set<String> { Set(indexes.byEquipment.keys) }
}

private struct DatabaseIndexes: Sendable {
    let all: [Exercise]
    let byMuscle: [String: [String]]
    let byMovementPattern: [String: [String]]
    let byEquipment: [String: [String]]

    init(exercises: [String: Exercise]) {
        let sorted = exercises.values.sorted { $0.exerciseId < $1.exerciseId }
        self.all = sorted
        var muscles: [String: [String]] = [:]
        var patterns: [String: [String]] = [:]
        var equipment: [String: [String]] = [:]
        for exercise in sorted {
            let ids = Set(exercise.annotation.direct + exercise.annotation.indirect + exercise.annotation.stabilizers)
            for muscle in ids { muscles[muscle, default: []].append(exercise.exerciseId) }
            for pattern in exercise.annotation.patterns {
                patterns[pattern, default: []].append(exercise.exerciseId)
            }
            if case .string(let value)? = exercise.source?["equipment"] {
                equipment[value, default: []].append(exercise.exerciseId)
            }
        }
        self.byMuscle = muscles
        self.byMovementPattern = patterns
        self.byEquipment = equipment
    }
}

public struct Quantity: Codable, Sendable, Equatable { public let value: Double; public let unit: String; public init(value: Double, unit: String) { self.value = value; self.unit = unit } }
public struct SetObservation: Codable, Sendable, Equatable { public let setNumber: Int?; public let setType: String; public let setPrescriptionId: String?; public let reps: Int?; public let load: Quantity?; public let completed: Bool; public let rpe: Double?; public let rir: Double?; public let resistance: [String: JSONValue]?; public init(setNumber: Int? = nil, setType: String, setPrescriptionId: String? = nil, reps: Int? = nil, load: Quantity? = nil, completed: Bool, rpe: Double? = nil, rir: Double? = nil, resistance: [String: JSONValue]? = nil) { self.setNumber = setNumber; self.setType = setType; self.setPrescriptionId = setPrescriptionId; self.reps = reps; self.load = load; self.completed = completed; self.rpe = rpe; self.rir = rir; self.resistance = resistance } }
public struct Substitution: Codable, Sendable, Equatable { public let reason: String; public let plannedExerciseId: String?; public let plannedPrescriptionId: String?; public let notes: String?; public init(reason: String, plannedExerciseId: String? = nil, plannedPrescriptionId: String? = nil, notes: String? = nil) { self.reason = reason; self.plannedExerciseId = plannedExerciseId; self.plannedPrescriptionId = plannedPrescriptionId; self.notes = notes } }
public struct ExerciseObservation: Codable, Sendable, Equatable { public let exerciseId: String?; public let exerciseName: String?; public let exercisePrescriptionId: String?; public let order: Int?; public let laterality: String?; public let substitution: Substitution?; public let sets: [SetObservation]; public init(exerciseId: String?, exerciseName: String? = nil, order: Int? = nil, laterality: String? = nil, sets: [SetObservation], exercisePrescriptionId: String? = nil, substitution: Substitution? = nil) { self.exerciseId = exerciseId; self.exerciseName = exerciseName; self.exercisePrescriptionId = exercisePrescriptionId; self.order = order; self.laterality = laterality; self.substitution = substitution; self.sets = sets }; public var isUnplanned: Bool { exercisePrescriptionId == nil && substitution == nil } }
public struct PlanReference: Codable, Sendable, Equatable { public let planId: String?; public let revisionId: String?; public let planSessionId: String?; public init(planId: String? = nil, revisionId: String? = nil, planSessionId: String? = nil) { self.planId = planId; self.revisionId = revisionId; self.planSessionId = planSessionId } }
public struct Workout: Codable, Sendable, Equatable {
    public let schemaVersion: String; public let sessionId: String; public let athleteId: String?; public let startTime: String; public let endTime: String?; public let planReference: PlanReference?; public let exercises: [ExerciseObservation]
    public init(schemaVersion: String, sessionId: String, startTime: String, endTime: String? = nil, exercises: [ExerciseObservation], athleteId: String? = nil, planReference: PlanReference? = nil) { self.schemaVersion = schemaVersion; self.sessionId = sessionId; self.athleteId = athleteId; self.startTime = startTime; self.endTime = endTime; self.planReference = planReference; self.exercises = exercises }
    public static func load(url: URL, decoder: JSONDecoder = JSONDecoder()) throws -> Workout { do { return try decoder.decode(Workout.self, from: Data(contentsOf: url)) } catch { throw FEDBError.invalidDocument("Unable to decode workout: \(error)") } }
    public func effectiveSets(using database: FEDatabase) -> [String: Double] { var totals: [String: Double] = [:]; for observation in exercises { guard let id = observation.exerciseId, let exercise = try? database.getExercise(id), exercise.annotation.volumeEligible else { continue }; let credits = database.setCredits; let counted = Set(["working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"]); let sets = Double(observation.sets.filter { $0.completed && counted.contains($0.setType) }.count); for muscle in exercise.annotation.direct { totals[muscle, default: 0] += sets * credits.direct }; for muscle in exercise.annotation.indirect { totals[muscle, default: 0] += sets * credits.indirect }; for muscle in exercise.annotation.stabilizers { totals[muscle, default: 0] += sets * credits.stabilizer } }; return totals }
}

public struct PlanCycle: Codable, Sendable, Equatable { public let lengthDays: Int; public init(lengthDays: Int) { self.lengthDays = lengthDays } }
public struct PlanPhase: Codable, Sendable, Equatable { public let phaseId: String; public let durationCycles: Int; public let cycle: PlanCycle?; public init(phaseId: String, durationCycles: Int, cycle: PlanCycle? = nil) { self.phaseId = phaseId; self.durationCycles = durationCycles; self.cycle = cycle } }
public struct PlannedSet: Codable, Sendable, Equatable { public let setPrescriptionId: String; public let setType: String; public let reps: JSONValue; public let load: JSONValue?; public var effort: JSONValue? = nil; public var notes: String? = nil; public init(setPrescriptionId: String, setType: String, reps: JSONValue, load: JSONValue? = nil, effort: JSONValue? = nil, notes: String? = nil) { self.setPrescriptionId = setPrescriptionId; self.setType = setType; self.reps = reps; self.load = load; self.effort = effort; self.notes = notes } }
public struct PlanExercisePrescription: Codable, Sendable, Equatable { public let prescriptionId: String; public let exerciseId: String?; public let exerciseName: String?; public var externalExerciseId: JSONValue? = nil; public let order: Int?; public let sets: JSONValue?; public let reps: JSONValue?; public var load: JSONValue? = nil; public var effort: JSONValue? = nil; public var setType: String? = nil; public var laterality: String? = nil; public var notes: String? = nil; public let plannedSets: [PlannedSet]?; public let progression: JSONValue?; public let optional: Bool?; public let condition: String?; public init(prescriptionId: String, exerciseId: String? = nil, exerciseName: String? = nil, externalExerciseId: JSONValue? = nil, order: Int? = nil, sets: JSONValue? = nil, reps: JSONValue? = nil, load: JSONValue? = nil, effort: JSONValue? = nil, setType: String? = nil, laterality: String? = nil, notes: String? = nil, plannedSets: [PlannedSet]? = nil, progression: JSONValue? = nil, optional: Bool? = nil, condition: String? = nil) { self.prescriptionId = prescriptionId; self.exerciseId = exerciseId; self.exerciseName = exerciseName; self.externalExerciseId = externalExerciseId; self.order = order; self.sets = sets; self.reps = reps; self.load = load; self.effort = effort; self.setType = setType; self.laterality = laterality; self.notes = notes; self.plannedSets = plannedSets; self.progression = progression; self.optional = optional; self.condition = condition } }
public struct PlanSession: Codable, Sendable, Equatable { public let planSessionId: String; public let phaseId: String?; public let dayOffset: Int; public var name: String? = nil; public var notes: String? = nil; public let exercises: [PlanExercisePrescription]; public init(planSessionId: String, phaseId: String? = nil, dayOffset: Int, name: String? = nil, notes: String? = nil, exercises: [PlanExercisePrescription]) { self.planSessionId = planSessionId; self.phaseId = phaseId; self.dayOffset = dayOffset; self.name = name; self.notes = notes; self.exercises = exercises } }
public struct WorkoutPlan: Codable, Sendable, Equatable {
    public let schemaVersion: String; public let planId: String; public let revisionId: String; public let name: String?; public var description: String? = nil; public var provenance: JSONValue? = nil; public let cycle: PlanCycle; public var notes: String? = nil; public var tags: [String]? = nil; public let phases: [PlanPhase]?; public let sessions: [PlanSession]
    private let descriptionWasPresent: Bool
    public init(schemaVersion: String = "0.2.0", planId: String, revisionId: String, name: String? = nil, description: String? = nil, provenance: JSONValue? = nil, cycle: PlanCycle, notes: String? = nil, tags: [String]? = nil, phases: [PlanPhase]? = nil, sessions: [PlanSession]) { self.schemaVersion = schemaVersion; self.planId = planId; self.revisionId = revisionId; self.name = name; self.description = description; self.descriptionWasPresent = description != nil; self.provenance = provenance; self.cycle = cycle; self.notes = notes; self.tags = tags; self.phases = phases; self.sessions = sessions }
    private enum CodingKeys: String, CodingKey { case schemaVersion, planId, revisionId, name, description, provenance, cycle, notes, tags, phases, sessions }
    public init(from decoder: Decoder) throws {
        let c = try decoder.container(keyedBy: CodingKeys.self)
        schemaVersion = try c.decode(String.self, forKey: .schemaVersion); planId = try c.decode(String.self, forKey: .planId); revisionId = try c.decode(String.self, forKey: .revisionId)
        name = try c.decodeIfPresent(String.self, forKey: .name); description = try c.decodeIfPresent(String.self, forKey: .description); descriptionWasPresent = c.contains(.description)
        provenance = try c.decodeIfPresent(JSONValue.self, forKey: .provenance); cycle = try c.decode(PlanCycle.self, forKey: .cycle)
        notes = try c.decodeIfPresent(String.self, forKey: .notes); tags = try c.decodeIfPresent([String].self, forKey: .tags); phases = try c.decodeIfPresent([PlanPhase].self, forKey: .phases); sessions = try c.decode([PlanSession].self, forKey: .sessions)
    }
    public func encode(to encoder: Encoder) throws {
        var c = encoder.container(keyedBy: CodingKeys.self)
        try c.encode(schemaVersion, forKey: .schemaVersion); try c.encode(planId, forKey: .planId); try c.encode(revisionId, forKey: .revisionId)
        try c.encodeIfPresent(name, forKey: .name); if descriptionWasPresent { try c.encode(description, forKey: .description) }; try c.encodeIfPresent(provenance, forKey: .provenance)
        try c.encode(cycle, forKey: .cycle); try c.encodeIfPresent(notes, forKey: .notes); try c.encodeIfPresent(tags, forKey: .tags)
        try c.encodeIfPresent(phases, forKey: .phases); try c.encode(sessions, forKey: .sessions)
    }
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
