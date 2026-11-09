// Privacy scan for video frames (HV-07). macOS Vision OCR over PNG/JPG files; prints every recognised line that looks like
// an e-mail address, a loopback address, a token-shaped string or a Google account hint. Exit code 1 when anything matched.
//
//   swiftc -O demo/video/capture/ocr-scan.swift -o /tmp/mdm-footage/ocr-scan
//   /tmp/mdm-footage/ocr-scan frame1.png frame2.png ...        (recognition languages: English and Korean)
//
// Lines with "scontent"/"fbcdn" are the signed image links of the real Slides run (demo art, expired): they are not reported.
import AppKit
import Foundation
import Vision

let patterns: [(String, NSRegularExpression)] = [
  ("email", try! NSRegularExpression(pattern: "[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}")),
  ("loopback", try! NSRegularExpression(pattern: "localhost|127\\.0\\.0\\.1|:3847|:5174")),
  ("token", try! NSRegularExpression(pattern: "sk_[0-9a-f]{16,}|Bearer\\s+\\S{12,}|DMEM_TOKEN|[A-Za-z0-9_-]{40,}")),
  ("account", try! NSRegularExpression(pattern: "(?i)gmail\\.com|@gmail|google account|구글 계정"))
]
var findings = 0, scanned = 0, totalLines = 0
for path in CommandLine.arguments.dropFirst() {
  guard let image = NSImage(contentsOfFile: path), let cg = image.cgImage(forProposedRect: nil, context: nil, hints: nil) else { print("unreadable: \(path)"); findings += 1; continue }
  let request = VNRecognizeTextRequest()
  request.recognitionLevel = .accurate
  request.recognitionLanguages = ["en-US", "ko-KR"]
  request.usesLanguageCorrection = false
  do { try VNImageRequestHandler(cgImage: cg, options: [:]).perform([request]) } catch { print("ocr failed: \(path)"); findings += 1; continue }
  let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
  scanned += 1; totalLines += lines.count
  for line in lines where !line.contains("scontent") && !line.contains("fbcdn") {
    for (name, re) in patterns where re.firstMatch(in: line, range: NSRange(line.startIndex..., in: line)) != nil {
      print("\(path): [\(name)] \(line)"); findings += 1
    }
  }
}
print("scanned \(scanned) image(s), \(totalLines) text lines, \(findings) finding(s)")
exit(findings == 0 ? 0 : 1)
