import Foundation

public struct PlanCoverageReport: Sendable, Equatable {
    public let nativePeriodDays: Int
    public let directSets: [String: Double]
    public let indirectSets: [String: Double]
    public let effectiveSets: [String: Double]
    public let mappedSets: Double
    public let unmappedSets: Double

    public init(nativePeriodDays: Int, directSets: [String: Double], indirectSets: [String: Double], mappedSets: Double, unmappedSets: Double) {
        self.nativePeriodDays = nativePeriodDays
        self.directSets = directSets
        self.indirectSets = indirectSets
        self.effectiveSets = Set(directSets.keys).union(indirectSets.keys).reduce(into: [:]) { result, muscle in
            result[muscle] = (directSets[muscle] ?? 0) + (indirectSets[muscle] ?? 0) * 0.5
        }
        self.mappedSets = mappedSets
        self.unmappedSets = unmappedSets
    }
}

public extension WorkoutPlan {
    /// Deterministic native-cycle PLAN coverage using DB++'s 1.0/0.5/0.0 credits.
    func coverage(using database: FEDatabase) -> PlanCoverageReport {
        var direct: [String: Double] = [:]
        var indirect: [String: Double] = [:]
        var mapped = 0.0
        var unmapped = 0.0
        for session in sessions {
            for prescription in session.exercises {
                let count = prescription.plannedSets.map { Double($0.count) } ?? number(from: prescription.sets)
                guard let id = prescription.exerciseId, let exercise = try? database.getExercise(id), exercise.annotation.volumeEligible else {
                    unmapped += count
                    continue
                }
                mapped += count
                for muscle in exercise.annotation.direct { direct[muscle, default: 0] += count }
                for muscle in exercise.annotation.indirect { indirect[muscle, default: 0] += count }
            }
        }
        return PlanCoverageReport(nativePeriodDays: cycle.lengthDays, directSets: direct, indirectSets: indirect, mappedSets: mapped, unmappedSets: unmapped)
    }
}

private func number(from value: JSONValue?) -> Double {
    guard let value else { return 0 }
    if case .number(let number) = value { return number }
    if case .object(let object) = value, case .number(let target)? = object["target"] { return target }
    return 0
}
