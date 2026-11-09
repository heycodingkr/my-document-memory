// Lists on-screen windows of one application as JSON lines: id, owner, title, bounds (points), layer.
// Used to find the macOS window id of the Arise window the capture drives, so that `screencapture -l <id>` records that window
// alone (what is on top of it does not matter).
//
//   swiftc -O demo/video/capture/windows.swift -o /tmp/mdm-footage/windows
//   /tmp/mdm-footage/windows Arise            (owner name filter, case-insensitive; no argument lists everything)
import CoreGraphics
import Foundation

let args = Array(CommandLine.arguments.dropFirst())
let includeAll = args.contains("--all")          // also windows that are minimized or on another Space
let filter = args.first(where: { !$0.hasPrefix("--") })?.lowercased()
let options: CGWindowListOption = includeAll ? [.optionAll] : [.optionOnScreenOnly, .excludeDesktopElements]
guard let list = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] else { exit(1) }
for w in list {
  let owner = (w[kCGWindowOwnerName as String] as? String) ?? ""
  if let f = filter, !owner.lowercased().contains(f) { continue }
  let b = (w[kCGWindowBounds as String] as? [String: Double]) ?? [:]
  let item: [String: Any] = [
    "id": (w[kCGWindowNumber as String] as? Int) ?? -1,
    "owner": owner,
    "title": (w[kCGWindowName as String] as? String) ?? "",
    "layer": (w[kCGWindowLayer as String] as? Int) ?? -1,
    "onscreen": (w[kCGWindowIsOnscreen as String] as? Bool) ?? false,
    "x": b["X"] ?? 0, "y": b["Y"] ?? 0, "w": b["Width"] ?? 0, "h": b["Height"] ?? 0
  ]
  if let data = try? JSONSerialization.data(withJSONObject: item, options: [.sortedKeys]), let s = String(data: data, encoding: .utf8) { print(s) }
}
