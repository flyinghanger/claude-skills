import Vision
import AppKit
import Foundation

guard CommandLine.arguments.count > 1 else {
    fputs("Usage: vision_ocr <image_path> [image_path2 ...]\n", stderr)
    exit(1)
}

let paths = Array(CommandLine.arguments.dropFirst())

for path in paths {
    guard let image = NSImage(contentsOfFile: path),
          let cgImage = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        fputs("Failed to load: \(path)\n", stderr)
        continue
    }

    let sem = DispatchSemaphore(value: 0)
    let request = VNRecognizeTextRequest { request, error in
        if let error = error {
            fputs("Error: \(error.localizedDescription)\n", stderr)
            sem.signal()
            return
        }
        guard let observations = request.results as? [VNRecognizedTextObservation] else {
            sem.signal()
            return
        }
        print("=== \(path) ===")
        for obs in observations {
            if let text = obs.topCandidates(1).first?.string {
                print(text)
            }
        }
        print("")
        sem.signal()
    }
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "zh-Hant", "en"]
    request.usesLanguageCorrection = true

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try? handler.perform([request])
    sem.wait()
}
