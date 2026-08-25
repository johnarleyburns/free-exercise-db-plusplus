import Foundation

public struct PlanCoverageView: Sendable, Equatable {
    public let periodDays: Int
    public let directSets: [String: Double]
    public let indirectSets: [String: Double]
    public let stabilizerParticipationSets: [String: Double]
    public let effectiveSets: [String: Double]
    public let movementPatternSets: [String: Double]
}

public struct PlanCoverageCompleteness: Sendable, Equatable {
    public let plannedSets: Double
    public let mappedSets: Double
    public let unmappedSets: Double
    public let ineligibleSets: Double
    public var mappedFraction: Double { plannedSets == 0 ? 1 : mappedSets / plannedSets }
}

public struct PlanCoverageReport: Sendable, Equatable {
    public let nativeCycle: PlanCoverageView
    public let normalized7Day: PlanCoverageView
    public let coverageCompleteness: PlanCoverageCompleteness
    public let phaseSpecific: [String: PlanCoverageView]
    public var nativePeriodDays: Int { nativeCycle.periodDays }
    public var directSets: [String: Double] { nativeCycle.directSets }
    public var indirectSets: [String: Double] { nativeCycle.indirectSets }
    public var stabilizerParticipationSets: [String: Double] { nativeCycle.stabilizerParticipationSets }
    public var effectiveSets: [String: Double] { nativeCycle.effectiveSets }
    public var movementPatternSets: [String: Double] { nativeCycle.movementPatternSets }
    public var mappedSets: Double { coverageCompleteness.mappedSets }
    public var unmappedSets: Double { coverageCompleteness.unmappedSets }
}

public extension WorkoutPlan {
    /// Deterministic PLAN coverage using DB++'s 1.0/0.5/0.0 credits.
    func coverage(using database: FEDatabase) -> PlanCoverageReport {
        let native = coverageView(for: sessions, periodDays: cycle.lengthDays, using: database)
        let scale = 7.0 / Double(cycle.lengthDays)
        let normalized = scaled(native.view, by: scale, periodDays: 7)
        var phaseViews: [String: PlanCoverageView] = [:]
        for phase in phases ?? [] {
            let phaseSessions = sessions.filter { $0.phaseId == phase.phaseId }
            let days = phase.cycle?.lengthDays ?? cycle.lengthDays
            phaseViews[phase.phaseId] = coverageView(for: phaseSessions, periodDays: days, using: database).view
        }
        return PlanCoverageReport(nativeCycle: native.view, normalized7Day: normalized, coverageCompleteness: native.completeness, phaseSpecific: phaseViews)
    }

    private func coverageView(for selected: [PlanSession], periodDays: Int, using database: FEDatabase) -> (view: PlanCoverageView, completeness: PlanCoverageCompleteness) {
        var direct: [String: Double] = [:], indirect: [String: Double] = [:], stabilizers: [String: Double] = [:], patterns: [String: Double] = [:]
        var planned = 0.0, mapped = 0.0, unmapped = 0.0, ineligible = 0.0
        for session in selected { for prescription in session.exercises {
            let count = prescription.plannedSets.map { Double($0.count) } ?? number(from: prescription.sets)
            planned += count
            guard let id = prescription.exerciseId, let exercise = try? database.getExercise(id) else { unmapped += count; continue }
            mapped += count
            if !exercise.annotation.volumeEligible { ineligible += count }
            for muscle in exercise.annotation.direct { direct[muscle, default: 0] += count }
            for muscle in exercise.annotation.indirect { indirect[muscle, default: 0] += count }
            for muscle in exercise.annotation.stabilizers { stabilizers[muscle, default: 0] += count }
            for pattern in exercise.annotation.patterns { patterns[pattern, default: 0] += count }
        }}
        let muscles = Set(direct.keys).union(indirect.keys).union(stabilizers.keys)
        let effective = muscles.reduce(into: [String: Double]()) { $0[$1] = (direct[$1] ?? 0) + (indirect[$1] ?? 0) * 0.5 }
        return (PlanCoverageView(periodDays: periodDays, directSets: direct, indirectSets: indirect, stabilizerParticipationSets: stabilizers, effectiveSets: effective, movementPatternSets: patterns), PlanCoverageCompleteness(plannedSets: planned, mappedSets: mapped, unmappedSets: unmapped, ineligibleSets: ineligible))
    }
}

private func scaled(_ view: PlanCoverageView, by scale: Double, periodDays: Int) -> PlanCoverageView {
    func values(_ input: [String: Double]) -> [String: Double] { input.mapValues { $0 * scale } }
    return PlanCoverageView(periodDays: periodDays, directSets: values(view.directSets), indirectSets: values(view.indirectSets), stabilizerParticipationSets: values(view.stabilizerParticipationSets), effectiveSets: values(view.effectiveSets), movementPatternSets: values(view.movementPatternSets))
}

private func number(from value: JSONValue?) -> Double {
    guard let value else { return 0 }
    if case .number(let number) = value { return number }
    if case .object(let object) = value {
        for key in ["target", "min", "max"] { if case .number(let result)? = object[key] { return result } }
    }
    return 0
}
