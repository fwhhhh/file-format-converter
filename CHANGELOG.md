# Changelog

## 0.7.0

- Extract subtitle tracks to SRT and choose the audio track used for video
  conversions
- Show audio/subtitle track counts on video cards; only offer SRT when the
  video really contains subtitles
- Add image maximum size and video resolution settings
- Media tests for multi-track and subtitle handling

## 0.6.1

- Rebuild OCR Word documents with page size, paragraph grouping, indents,
  approximate font sizes and a low-confidence noise filter
- Add filename templates (`{name}`, `{target}`, `{date}`, `{time}`) alongside
  the existing suffix option
- Request Tesseract TSV output without requiring a config file

## 0.6.0

- Convert scanned PDFs to editable Word text with `DOCX · OCR`
- Add an output filename suffix setting
- Add a Windows GitHub Actions test workflow

## 0.5.0

- PDF toolbox: merge, split, extract pages, images to multi-page PDF and
  PDF to images with page ranges and DPI
- Per-file percentage progress, cancel button and taskbar completion alert
- Fix the full build by copying document tools after PyInstaller instead of
  passing them through `--add-data`

## 0.4.0

- LibreOffice fallback for Word/Excel/PowerPoint conversions
- Calibre e-book conversions for epub, mobi and azw3
- `--full` build mode bundling LibreOffice, Pandoc, Tesseract and Calibre

## 0.3.0

- Pandoc document conversions (Markdown/HTML/text ↔ docx/odt/rtf/epub)
- Tesseract OCR fallback for scanned PDFs
- Bundle Chinese/English OCR language data

## 0.2.0

- Microsoft Office conversions: docx/xlsx/pptx → PDF, PDF → Word
- PDF → PNG/JPG page images and PDF → text
- Engine status dialog for Word, Excel, PowerPoint and PDF

## 0.1.0

- Initial release: images (including HEIC), audio/video, archives, text and
  spreadsheets
- Minimal drag-and-drop interface with per-file target format selection
- Chinese/English UI, light/dark/system themes, portable PyInstaller build
