import Foundation
import FreeExerciseDBPlusPlus
import FITSwiftSDK

/// Garmin FIT Activity adapter for DB++ ACTUAL documents.
///
/// The complete DB++ JSON is carried in a self-describing FIT developer field
/// on the Session message. Standard Activity/File Id/Session/Lap messages are
/// emitted as a useful native projection. Consumers that do not understand the
/// developer field still receive a valid strength Activity summary.
public struct GarminFITAdapter: Sendable {
    public init() {}

    public func exportActivity(workoutJSON: Data) throws -> Data {
        let workout = try HealthInterop.canonicalWorkout(from: workoutJSON)
        guard let fields = workout.objectValue,
              case .string(let startText)? = fields["startTime"],
              case .string(let sessionId)? = fields["sessionId"],
              let startDate = ISO8601DateFormatter().date(from: startText) else {
            throw HealthInteropError.invalidWorkout("DB++ ACTUAL requires an ISO-8601 startTime and sessionId")
        }
        let start = DateTime(date: startDate)
        let endDate: Date
        if case .string(let endText)? = fields["endTime"], let parsed = ISO8601DateFormatter().date(from: endText) { endDate = parsed }
        else { endDate = startDate }
        let end = DateTime(date: endDate)
        let elapsed = Float64(max(0, end.timestamp >= start.timestamp ? end.timestamp - start.timestamp : 0))
        let canonical = String(data: workoutJSON, encoding: .utf8) ?? ""

        let developerId = DeveloperDataIdMesg()
        let appId: [UInt8] = [0x46, 0x45, 0x44, 0x42, 0x50, 0x50, 0x2D, 0x48, 0x45, 0x41, 0x4C, 0x54, 0x48, 0x2D, 0x31, 0x00]
        for (index, value) in appId.enumerated() { try developerId.setApplicationId(index: index, value: value) }
        try developerId.setDeveloperDataIndex(0)
        try developerId.setApplicationVersion(1)

        // FIT string fields have a bounded field size. Chunk the canonical
        // document across self-describing developer fields so large ACTUAL
        // documents remain lossless instead of being silently truncated.
        let chunkSize = 180
        var chunks: [String] = []
        var cursor = canonical.startIndex
        while cursor < canonical.endIndex {
            let start = cursor
            var byteCount = 0
            while cursor < canonical.endIndex {
                let characterBytes = canonical[cursor].utf8.count
                if byteCount > 0 && byteCount + characterBytes > chunkSize { break }
                byteCount += characterBytes
                cursor = canonical.index(after: cursor)
            }
            chunks.append(String(canonical[start..<cursor]))
        }
        if chunks.isEmpty { chunks = [""] }
        var descriptions: [FieldDescriptionMesg] = []
        var fields: [DeveloperField] = []
        for (index, chunk) in chunks.enumerated() {
            let description = FieldDescriptionMesg()
            try description.setDeveloperDataIndex(0)
            try description.setFieldDefinitionNumber(UInt8(index))
            try description.setFitBaseTypeId(.string)
            try description.setFieldName(index: 0, value: String(format: "DBPP JSON %03d", index))
            try description.setUnits(index: 0, value: "json")
            try description.setNativeMesgNum(.session)
            let field = DeveloperField(fieldDescription: description, developerDataIdMesg: developerId)
            try field.setValue(index: 0, value: chunk)
            descriptions.append(description); fields.append(field)
        }

        let serial = stableSerialNumber(sessionId)
        let fileId = FileIdMesg()
        try fileId.setType(.activity)
        try fileId.setManufacturer(.development)
        try fileId.setProduct(0)
        try fileId.setTimeCreated(start)
        try fileId.setSerialNumber(serial)

        let device = DeviceInfoMesg()
        try device.setDeviceIndex(.creator)
        try device.setManufacturer(.development)
        try device.setProduct(0)
        try device.setProductName("FEDB++")
        try device.setSerialNumber(serial)
        try device.setSoftwareVersion(1)
        try device.setTimestamp(start)

        let eventStart = EventMesg()
        try eventStart.setTimestamp(start); try eventStart.setEvent(.timer); try eventStart.setEventType(.start)
        let lap = LapMesg()
        try lap.setMessageIndex(0); try lap.setTimestamp(end); try lap.setStartTime(start)
        try lap.setTotalElapsedTime(elapsed); try lap.setTotalTimerTime(elapsed)
        try lap.setSport(.strengthTraining); try lap.setSubSport(.strengthTraining)

        let session = SessionMesg()
        try session.setMessageIndex(0); try session.setTimestamp(end); try session.setStartTime(start)
        try session.setTotalElapsedTime(elapsed); try session.setTotalTimerTime(elapsed)
        try session.setSport(.strengthTraining); try session.setSubSport(.strengthTraining)
        try session.setFirstLapIndex(0); try session.setNumLaps(1)
        fields.forEach { session.setDeveloperField($0) }

        let eventStop = EventMesg()
        try eventStop.setTimestamp(end); try eventStop.setEvent(.timer); try eventStop.setEventType(.stopAll)
        let activity = ActivityMesg()
        try activity.setTimestamp(end); try activity.setTotalTimerTime(elapsed); try activity.setNumSessions(1)
        try activity.setLocalTimestamp(LocalDateTime(Int(end.timestamp) + TimeZone.current.secondsFromGMT()))

        let encoder = Encoder()
        encoder.write(mesg: fileId); encoder.write(mesg: device); encoder.write(mesg: developerId)
        descriptions.forEach { encoder.write(mesg: $0) }; encoder.write(mesg: eventStart)
        encoder.write(mesg: lap); encoder.write(mesg: session); encoder.write(mesg: eventStop); encoder.write(mesg: activity)
        return encoder.close()
    }

    public func importActivity(_ data: Data, mode: HealthInteropMode = .strict) throws -> Data {
        let decoder = Decoder(stream: FITSwiftSDK.InputStream(data: data))
        guard try decoder.isFIT() else { throw HealthInteropError.invalidEnvelope("input is not a FIT file") }
        let listener = FitListener()
        decoder.addMesgListener(listener)
        try decoder.read()
        for session in listener.fitMessages.sessionMesgs {
            let chunks = session.developerFields.compactMap { field -> (Int, String)? in
                let name = field.getName()
                guard name.hasPrefix("DBPP JSON "), let index = Int(name.dropFirst("DBPP JSON ".count)), let value = field.getValue() as? String else { return nil }
                return (index, value)
            }.sorted { $0.0 < $1.0 }
            if !chunks.isEmpty {
                let raw = chunks.map(\.1).joined()
                guard let canonical = raw.data(using: .utf8) else { continue }
                _ = try HealthInterop.canonicalWorkout(from: canonical)
                return canonical
            }
        }
        throw HealthInteropError.lossyImport([HealthInteropLoss(path: "Session.developerFields", reason: "FIT file has no DB++ canonical sidecar", destination: "full DB++ ACTUAL")])
    }

    private func stableSerialNumber(_ value: String) -> UInt32 {
        var hash: UInt32 = 2166136261
        for byte in value.utf8 { hash = (hash ^ UInt32(byte)) &* 16777619 }
        return hash == 0 ? 1 : hash
    }
}
