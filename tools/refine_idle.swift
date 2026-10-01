import AppKit
import Foundation

// Keep the source JPEG's character pixels. The previous cutout supplies only
// an alpha mask and the crop is registered against the new source image.
let root = URL(fileURLWithPath: "/Users/mac/Documents/dsh/naiwa-fart")
let sourceURL = URL(fileURLWithPath: "/Users/mac/Pictures/奶蛙总文件夹/奶蛙-角色设定/奶蛙-基础全身形象.jpg")
let maskURL = root.appendingPathComponent("assets/src/player_idle_mask.png")
let fullURL = URL(fileURLWithPath: "/Users/mac/Pictures/奶蛙总文件夹/奶蛙-角色设定/奶蛙-基础全身形象-透明抠图.png")
let cropURL = root.appendingPathComponent("assets/src/player_idle.png")

func load(_ url: URL) throws -> NSBitmapImageRep {
    let data = try Data(contentsOf: url)
    guard let image = NSBitmapImageRep(data: data) else { throw NSError(domain: "image", code: 1) }
    return image
}

func rgb(_ image: NSBitmapImageRep, _ x: Int, _ y: Int) -> (Double, Double, Double, Double) {
    guard let color = image.colorAt(x: x, y: y)?.usingColorSpace(.deviceRGB) else { return (1, 1, 1, 0) }
    return (color.redComponent, color.greenComponent, color.blueComponent, color.alphaComponent)
}

func output(_ w: Int, _ h: Int) -> NSBitmapImageRep {
    return NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h,
                            bitsPerSample: 8, samplesPerPixel: 4, hasAlpha: true,
                            isPlanar: false, colorSpaceName: .deviceRGB,
                            bytesPerRow: 0, bitsPerPixel: 0)!
}

func save(_ image: NSBitmapImageRep, _ url: URL) throws {
    guard let data = image.representation(using: .png, properties: [:]) else { throw NSError(domain: "png", code: 2) }
    try data.write(to: url, options: .atomic)
}

let src = try load(sourceURL)
let mask = try load(maskURL)
let sample: [(Int, Int)] = stride(from: 10, to: mask.pixelsHigh - 10, by: 14).flatMap { y in
    stride(from: 10, to: mask.pixelsWide - 10, by: 14).compactMap { x in
        rgb(mask, x, y).3 > 0.98 ? (x, y) : nil
    }
}
var best = (x: 0, y: 0, loss: Double.infinity)
for y0 in 0...(src.pixelsHigh - mask.pixelsHigh) {
    for x0 in 0...(src.pixelsWide - mask.pixelsWide) {
        var loss = 0.0
        for (x, y) in sample {
            let a = rgb(src, x + x0, y + y0)
            let b = rgb(mask, x, y)
            loss += abs(a.0 - b.0) + abs(a.1 - b.1) + abs(a.2 - b.2)
        }
        if loss < best.loss { best = (x0, y0, loss) }
    }
}
print("registered crop origin: \(best.x),\(best.y), loss: \(best.loss)")

let full = output(src.pixelsWide, src.pixelsHigh)
let crop = output(mask.pixelsWide, mask.pixelsHigh)
for y in 0..<mask.pixelsHigh {
    for x in 0..<mask.pixelsWide {
        let oldAlpha = rgb(mask, x, y).3
        let (r, g, b, _) = rgb(src, x + best.x, y + best.y)
        var alpha = oldAlpha < 0.045 ? 0.0 : oldAlpha
        let spread = max(r, g, b) - min(r, g, b)
        let lightness = (r + g + b) / 3
        // Connected neutral pale fringe at the silhouette is backdrop/shadow.
        if alpha < 0.9 && spread < 0.075 && lightness > 0.58 { alpha = 0 }
        // The source photo's floor shadow is a pale neutral patch below the
        // feet; the game draws its own ground shadow.
        if y + best.y > 420 && r > 0.7 && g > 0.64 && b > 0.53 { alpha = 0 }
        var rr = r, gg = g, bb = b
        if alpha > 0.07 && alpha < 0.98 {
            let white = 1 - alpha
            rr = max(0, min(1, (r - white) / alpha))
            gg = max(0, min(1, (g - white) / alpha))
            bb = max(0, min(1, (b - white) / alpha))
        }
        let color = NSColor(deviceRed: rr, green: gg, blue: bb, alpha: alpha)
        crop.setColor(color, atX: x, y: y)
        full.setColor(color, atX: x + best.x, y: y + best.y)
    }
}
try save(full, fullURL)
try save(crop, cropURL)
print("saved \(fullURL.path) and \(cropURL.path)")
