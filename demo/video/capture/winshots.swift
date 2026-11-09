// Frame grabber for one macOS window: CGWindowListCreateImage in a loop, cropped to a region, written as JPEG frames with a
// timestamp list. It works on windows that are hidden or covered (it reads the window's own surface), and unlike
// `screencapture -v` it does not hand back black frames for them.
//
//   swiftc -O demo/video/capture/winshots.swift -o /tmp/mdm-footage/winshots
//   /tmp/mdm-footage/winshots <windowId> <outDir> <fps> <maxSeconds> [x y w h]     (crop in window pixels, 2x Retina)
//   stop early with SIGINT/SIGTERM; <outDir>/frames.txt lists "<file> <seconds since start>" per frame
import CoreGraphics
import Foundation
import ImageIO
import UniformTypeIdentifiers

let a = CommandLine.arguments
guard a.count >= 5, let wid = UInt32(a[1]) else { print("usage: winshots <windowId> <outDir> <fps> <maxSeconds> [x y w h]"); exit(2) }
let dir = a[2]
let fps = Double(a[3]) ?? 12
let maxSeconds = Double(a[4]) ?? 60
var crop: CGRect? = nil
if a.count >= 9, let x = Double(a[5]), let y = Double(a[6]), let w = Double(a[7]), let h = Double(a[8]) { crop = CGRect(x: x, y: y, width: w, height: h) }
try? FileManager.default.createDirectory(atPath: dir, withIntermediateDirectories: true)
var stop = false
signal(SIGINT) { _ in stop = true }
signal(SIGTERM) { _ in stop = true }
var log = ""
let start = Date()
var n = 0
var lastHash = 0
while !stop && Date().timeIntervalSince(start) < maxSeconds {
  let t0 = Date()
  if var image = CGWindowListCreateImage(.null, .optionIncludingWindow, wid, [.boundsIgnoreFraming, .bestResolution]) {
    if let c = crop, let cropped = image.cropping(to: c) { image = cropped }
    let name = String(format: "f%06d.jpg", n)
    let url = URL(fileURLWithPath: dir).appendingPathComponent(name) as CFURL
    if let dest = CGImageDestinationCreateWithURL(url, UTType.jpeg.identifier as CFString, 1, nil) {
      CGImageDestinationAddImage(dest, image, [kCGImageDestinationLossyCompressionQuality: 0.88] as CFDictionary)
      if CGImageDestinationFinalize(dest) { log += "\(name) \(String(format: "%.3f", Date().timeIntervalSince(start)))\n"; n += 1 }
    }
  }
  let spent = Date().timeIntervalSince(t0)
  let wait = 1.0 / fps - spent
  if wait > 0 { Thread.sleep(forTimeInterval: wait) }
}
try? log.write(toFile: dir + "/frames.txt", atomically: true, encoding: .utf8)
print("frames: \(n) in \(String(format: "%.1f", Date().timeIntervalSince(start))) s")
