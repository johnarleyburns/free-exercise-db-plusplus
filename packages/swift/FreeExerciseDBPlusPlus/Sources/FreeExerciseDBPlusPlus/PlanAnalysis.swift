import Foundation

public struct PlanCoverageView: Sendable, Equatable {
    public let periodDays: Int
    public let directSetRanges: [String: TargetRange]
    public let indirectSetRanges: [String: TargetRange]
    public let stabilizerParticipationSetRanges: [String: TargetRange]
    public let effectiveSetRanges: [String: TargetRange]
    public let movementPatternSetRanges: [String: TargetRange]
    public let directSets: [String: Double]
    public let indirectSets: [String: Double]
    public let stabilizerParticipationSets: [String: Double]
    public let effectiveSets: [String: Double]
    public let movementPatternSets: [String: Double]
    public init(periodDays: Int, directSetRanges: [String: TargetRange] = [:], indirectSetRanges: [String: TargetRange] = [:], stabilizerParticipationSetRanges: [String: TargetRange] = [:], effectiveSetRanges: [String: TargetRange] = [:], movementPatternSetRanges: [String: TargetRange] = [:], directSets: [String: Double] = [:], indirectSets: [String: Double] = [:], stabilizerParticipationSets: [String: Double] = [:], effectiveSets: [String: Double] = [:], movementPatternSets: [String: Double] = [:]) {
        self.periodDays = periodDays; self.directSetRanges = directSetRanges; self.indirectSetRanges = indirectSetRanges; self.stabilizerParticipationSetRanges = stabilizerParticipationSetRanges; self.effectiveSetRanges = effectiveSetRanges; self.movementPatternSetRanges = movementPatternSetRanges; self.directSets = directSets; self.indirectSets = indirectSets; self.stabilizerParticipationSets = stabilizerParticipationSets; self.effectiveSets = effectiveSets; self.movementPatternSets = movementPatternSets
    }
}

public struct PlanCoverageCompleteness: Sendable, Equatable {
    public let plannedSets: Double
    public let plannedSetRange: TargetRange
    public let mappedSets: Double
    public let mappedSetRange: TargetRange
    public let unmappedSets: Double
    public let unmappedSetRange: TargetRange
    public let ineligibleSets: Double
    public let ineligibleSetRange: TargetRange
    public let unmappedPrescriptions: [String]
    public let ineligiblePrescriptions: [String]
    public var mappedFraction: Double { plannedSets == 0 ? 1 : mappedSets / plannedSets }
    public init(plannedSets: Double, plannedSetRange: TargetRange = TargetRange(), mappedSets: Double, mappedSetRange: TargetRange = TargetRange(), unmappedSets: Double, unmappedSetRange: TargetRange = TargetRange(), ineligibleSets: Double, ineligibleSetRange: TargetRange = TargetRange(), unmappedPrescriptions: [String] = [], ineligiblePrescriptions: [String] = []) {
        self.plannedSets = plannedSets; self.plannedSetRange = plannedSetRange; self.mappedSets = mappedSets; self.mappedSetRange = mappedSetRange; self.unmappedSets = unmappedSets; self.unmappedSetRange = unmappedSetRange; self.ineligibleSets = ineligibleSets; self.ineligibleSetRange = ineligibleSetRange; self.unmappedPrescriptions = unmappedPrescriptions; self.ineligiblePrescriptions = ineligiblePrescriptions
    }
}

public struct PlanExposureFrequency: Sendable, Equatable {
    public let exposuresPerNativeCycle: Double
    public let normalizedExposuresPer7Days: Double
}

public struct PlanCoverageReport: Sendable, Equatable {
    public let nativeCycle: PlanCoverageView
    public let normalized7Day: PlanCoverageView
    public let coverageCompleteness: PlanCoverageCompleteness
    public let phaseSpecific: [String: PlanCoverageView]
    public let exposureFrequency: [String: [String: PlanExposureFrequency]]
    public let analysisMetadata: [String: JSONValue]
    public let periodization: JSONValue?
    public init(nativeCycle: PlanCoverageView, normalized7Day: PlanCoverageView, coverageCompleteness: PlanCoverageCompleteness, phaseSpecific: [String: PlanCoverageView] = [:], exposureFrequency: [String: [String: PlanExposureFrequency]] = [:], analysisMetadata: [String: JSONValue] = [:], periodization: JSONValue? = nil) {
        self.nativeCycle = nativeCycle; self.normalized7Day = normalized7Day; self.coverageCompleteness = coverageCompleteness; self.phaseSpecific = phaseSpecific; self.exposureFrequency = exposureFrequency; self.analysisMetadata = analysisMetadata; self.periodization = periodization
    }
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
        var frequency: [String: [String: PlanExposureFrequency]] = ["muscles": [:], "movementPatterns": [:]]
        for (muscle, sessions) in native.muscleSessions { frequency["muscles"]?[muscle] = PlanExposureFrequency(exposuresPerNativeCycle: Double(sessions.count), normalizedExposuresPer7Days: Double(sessions.count) * 7.0 / Double(cycle.lengthDays)) }
        for (pattern, sessions) in native.patternSessions { frequency["movementPatterns"]?[pattern] = PlanExposureFrequency(exposuresPerNativeCycle: Double(sessions.count), normalizedExposuresPer7Days: Double(sessions.count) * 7.0 / Double(cycle.lengthDays)) }
        let metadata: [String: JSONValue] = ["analysisVersion": .string("1.0.0"), "analysisPolicy": .string("dbpp-default-volume-v1"), "dbSchemaVersion": database.metadata["schemaVersion"] ?? .null, "dbConverterVersion": database.metadata["converterVersion"] ?? .null, "dbUpstreamSha256": database.metadata["upstream"]?.objectValue?["sha256"] ?? .null, "planSchemaVersion": .string(schemaVersion), "setCredits": .object(["direct": .number(database.setCredits.direct), "indirect": .number(database.setCredits.indirect), "stabilizer": .number(database.setCredits.stabilizer)]), "nativePeriodDays": .number(Double(cycle.lengthDays)), "normalizedPeriodDays": .number(7), "rangePolicy": .string("target-then-min-then-max"), "unitPolicy": .string("dbpp-conservative-units-v1")]
        return PlanCoverageReport(nativeCycle: native.view, normalized7Day: normalized, coverageCompleteness: native.completeness, phaseSpecific: phaseViews, exposureFrequency: frequency, analysisMetadata: metadata)
    }

    private func coverageView(for selected: [PlanSession], periodDays: Int, using database: FEDatabase) -> (view: PlanCoverageView, completeness: PlanCoverageCompleteness, muscleSessions: [String: Set<String>], patternSessions: [String: Set<String>]) {
        var direct: [String: TargetRange] = [:], indirect: [String: TargetRange] = [:], stabilizers: [String: TargetRange] = [:], patterns: [String: TargetRange] = [:]
        var muscleSessions: [String: Set<String>] = [:], patternSessions: [String: Set<String>] = [:]
        var planned = zeroRange(), mapped = zeroRange(), unmapped = zeroRange(), ineligible = zeroRange(); var unmappedIDs: [String] = [], ineligibleIDs: [String] = []
        for session in selected { for prescription in session.exercises {
            let count = plannedRange(for: prescription); planned = add(planned, count)
            guard let id = prescription.exerciseId, let exercise = try? database.getExercise(id) else { unmapped = add(unmapped, count); unmappedIDs.append(prescription.prescriptionId); continue }
            mapped = add(mapped, count)
            if !exercise.annotation.volumeEligible { ineligible = add(ineligible, count); ineligibleIDs.append(prescription.prescriptionId); continue }
            for muscle in exercise.annotation.direct { direct[muscle] = add(direct[muscle] ?? zeroRange(), count); muscleSessions[muscle, default: []].insert(session.planSessionId) }
            for muscle in exercise.annotation.indirect { indirect[muscle] = add(indirect[muscle] ?? zeroRange(), count); muscleSessions[muscle, default: []].insert(session.planSessionId) }
            for muscle in exercise.annotation.stabilizers { stabilizers[muscle] = add(stabilizers[muscle] ?? zeroRange(), count) }
            for pattern in exercise.annotation.patterns { patterns[pattern] = add(patterns[pattern] ?? zeroRange(), count); patternSessions[pattern, default: []].insert(session.planSessionId) }
        }}
        let muscles = Set(direct.keys).union(indirect.keys).union(stabilizers.keys)
        let credits = database.setCredits
        let effective = muscles.reduce(into: [String: TargetRange]()) { $0[$1] = add(add(scale(direct[$1] ?? zeroRange(), credits.direct), scale(indirect[$1] ?? zeroRange(), credits.indirect)), scale(stabilizers[$1] ?? zeroRange(), credits.stabilizer)) }
        func scalars(_ ranges: [String: TargetRange]) -> [String: Double] { ranges.compactMapValues { $0.target ?? $0.min ?? $0.max } }
        let view = PlanCoverageView(periodDays: periodDays, directSetRanges: nonzero(direct), indirectSetRanges: nonzero(indirect), stabilizerParticipationSetRanges: nonzero(stabilizers), effectiveSetRanges: nonzero(effective), movementPatternSetRanges: nonzero(patterns), directSets: scalars(nonzero(direct)), indirectSets: scalars(nonzero(indirect)), stabilizerParticipationSets: scalars(nonzero(stabilizers)), effectiveSets: scalars(nonzero(effective)), movementPatternSets: scalars(nonzero(patterns)))
        let completeness = PlanCoverageCompleteness(plannedSets: scalar(planned) ?? 0, plannedSetRange: planned, mappedSets: scalar(mapped) ?? 0, mappedSetRange: mapped, unmappedSets: scalar(unmapped) ?? 0, unmappedSetRange: unmapped, ineligibleSets: scalar(ineligible) ?? 0, ineligibleSetRange: ineligible, unmappedPrescriptions: unmappedIDs.sorted(), ineligiblePrescriptions: ineligibleIDs.sorted())
        return (view: view, completeness: completeness, muscleSessions: muscleSessions, patternSessions: patternSessions)
    }
}

private func scaled(_ view: PlanCoverageView, by factor: Double, periodDays: Int) -> PlanCoverageView {
    func ranges(_ input: [String: TargetRange]) -> [String: TargetRange] { input.mapValues { scale($0, factor) } }
    func values(_ input: [String: TargetRange]) -> [String: Double] { ranges(input).compactMapValues { scalar($0) } }
    return PlanCoverageView(periodDays: periodDays, directSetRanges: ranges(view.directSetRanges), indirectSetRanges: ranges(view.indirectSetRanges), stabilizerParticipationSetRanges: ranges(view.stabilizerParticipationSetRanges), effectiveSetRanges: ranges(view.effectiveSetRanges), movementPatternSetRanges: ranges(view.movementPatternSetRanges), directSets: values(view.directSetRanges), indirectSets: values(view.indirectSetRanges), stabilizerParticipationSets: values(view.stabilizerParticipationSetRanges), effectiveSets: values(view.effectiveSetRanges), movementPatternSets: values(view.movementPatternSetRanges))
}

private func number(from value: JSONValue?) -> Double? { guard let value else { return nil }; if case .number(let number) = value { return number }; let object = value.objectValue ?? [:]; return number(from: object["target"]) ?? number(from: object["min"]) ?? number(from: object["max"]) }
private func plannedRange(for prescription: PlanExercisePrescription) -> TargetRange { if let sets = prescription.plannedSets { let count = Double(sets.filter { counted($0.setType) }.count); return TargetRange(min: count, target: count, max: count) }; if let setType = prescription.setType, !counted(setType) { return zeroRange() }; let value = prescription.sets; if let object = value?.objectValue { return TargetRange(min: number(from: object["min"]), target: number(from: object["target"]), max: number(from: object["max"])) }; let numberValue = number(from: value) ?? 0; return TargetRange(min: numberValue, target: numberValue, max: numberValue) }
private func counted(_ type: String) -> Bool { ["working", "backoff", "amrap", "drop", "cluster", "rest_pause", "assisted"].contains(type) }
private func zeroRange() -> TargetRange { TargetRange(min: 0, target: 0, max: 0) }
private func add(_ a: TargetRange, _ b: TargetRange) -> TargetRange { TargetRange(min: a.min.flatMap { lhs in b.min.map { rhs in lhs + rhs } }, target: a.target.flatMap { lhs in b.target.map { rhs in lhs + rhs } }, max: a.max.flatMap { lhs in b.max.map { rhs in lhs + rhs } }) }
private func scale(_ value: TargetRange, _ factor: Double) -> TargetRange { TargetRange(min: value.min.map { $0 * factor }, target: value.target.map { $0 * factor }, max: value.max.map { $0 * factor }) }
private func scalar(_ value: TargetRange) -> Double? { value.target ?? value.min ?? value.max }
private func nonzero(_ values: [String: TargetRange]) -> [String: TargetRange] { values.filter { scalar($0.value) != 0 } }
