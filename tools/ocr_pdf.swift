import AppKit
import Foundation
import PDFKit
import Vision

// macOS Vision transcription for scanned research documents. Check figures against the PDF.
guard CommandLine.arguments.count == 3 else {
    fatalError("Usage: swift tools/ocr_pdf.swift input.pdf output.txt")
}

let input = URL(fileURLWithPath: CommandLine.arguments[1])
let output = URL(fileURLWithPath: CommandLine.arguments[2])
guard let document = PDFDocument(url: input) else {
    fatalError("Cannot open the input PDF")
}

var pages: [String] = []
for index in 0..<document.pageCount {
    guard let page = document.page(at: index) else {
        fatalError("Missing PDF page")
    }
    let thumbnail = page.thumbnail(of: NSSize(width: 1700, height: 2400), for: .mediaBox)
    guard let image = thumbnail.cgImage(forProposedRect: nil, context: nil, hints: nil) else {
        fatalError("Cannot render the PDF page")
    }
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true
    request.customWords = ["猎德", "社工", "利民", "远洋明珠"]
    try VNImageRequestHandler(cgImage: image).perform([request])
    let lines = (request.results ?? []).compactMap { $0.topCandidates(1).first?.string }
    pages.append("[PDF第\(index + 1)页]\n" + lines.joined(separator: "\n"))
    print("OCR page \(index + 1)/\(document.pageCount)")
    fflush(stdout)
}

let notice = "自动OCR转写，仅用于全文检索。数字、表格及引用须对照原始PDF核验。\n\n"
try (notice + pages.joined(separator: "\n\n") + "\n").write(to: output, atomically: true, encoding: .utf8)
