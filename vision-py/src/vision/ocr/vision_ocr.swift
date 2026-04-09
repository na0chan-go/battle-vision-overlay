import Foundation
import Vision
import CoreGraphics
import ImageIO

func emit(_ object: [String: Any]) {
    let data = try! JSONSerialization.data(withJSONObject: object, options: [])
    let output = String(data: data, encoding: .utf8)!
    print(output)
}

guard CommandLine.arguments.count >= 2 else {
    emit(["texts": [], "error": "image path is required"])
    exit(1)
}

let imagePath = CommandLine.arguments[1]
let imageURL = URL(fileURLWithPath: imagePath)

guard let imageSource = CGImageSourceCreateWithURL(imageURL as CFURL, nil),
      let cgImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
    emit(["texts": [], "error": "failed to load image"])
    exit(1)
}

let request = VNRecognizeTextRequest()
request.recognitionLanguages = ["ja-JP", "en-US"]
request.recognitionLevel = .accurate
request.usesLanguageCorrection = false

let handler = VNImageRequestHandler(cgImage: cgImage)

do {
    try handler.perform([request])
} catch {
    emit(["texts": [], "error": "vision request failed: \(error.localizedDescription)"])
    exit(1)
}

let observations = (request.results ?? []).sorted { lhs, rhs in
    let yDelta = lhs.boundingBox.origin.y - rhs.boundingBox.origin.y
    if abs(yDelta) > 0.01 {
        return lhs.boundingBox.origin.y > rhs.boundingBox.origin.y
    }
    return lhs.boundingBox.origin.x < rhs.boundingBox.origin.x
}

let texts = observations.compactMap { observation -> [String: Any]? in
    guard let candidate = observation.topCandidates(1).first else {
        return nil
    }

    let text = candidate.string.trimmingCharacters(in: .whitespacesAndNewlines)
    guard !text.isEmpty else {
        return nil
    }

    return [
        "text": text,
        "confidence": candidate.confidence,
    ]
}

emit(["texts": texts, "error": NSNull()])
