# File Format Converter

[中文说明](README.zh-CN.md)

A small, minimal drag & drop file converter. Drop files or whole folders into
the window, tick the formats you want, and convert. One source file can be
converted to several formats at once, and any number of files can be processed
in one run.

See [CHANGELOG.md](CHANGELOG.md) for release history.

![Screenshot](docs/screenshot-en.png)

## Features

- Drag & drop files or folders anywhere in the window
- One collapsible card per file, with a list of valid target formats as chips
- Multi-select targets: `photo.jpg` + `PNG` + `PDF` produces both files
- Real format detection from file signatures, so renamed files still convert
  correctly
- Results show the actual output file icon, size and an "open folder" button
- Word, Excel and PowerPoint documents convert through the installed Microsoft
  Office, with LibreOffice as a free fallback; PDF files can be turned into Word,
  text or page images
- Pandoc handles Markdown / HTML / text ↔ docx / odt / rtf / epub, Tesseract OCR
  reads scanned PDFs into text or an editable OCR Word document (page size,
  paragraphs and approximate font sizes), and Calibre converts e-books
- Subtitle extraction (`srt`), audio-track selection for video conversions,
  image maximum size and video resolution settings
- Output filename template (`{name}`, `{target}`, `{date}`, `{time}`) and suffix,
  configurable in Settings
- PDF → Word without Microsoft Word: text-based PDFs are rebuilt with
  pdfplumber (page size, paragraphs, indents and approximate font sizes);
  scanned PDFs automatically fall back to OCR Word
- Optional Explorer context menu and Open with entries (installer tasks);
  files and folders passed on the command line are opened at startup, and
  opening more files reuses the existing window
- Startup check for newer GitHub releases (opens the release page; no silent
  self-update)
- PDF toolbox: merge PDFs, split by page or every N pages, extract page ranges,
  combine images into a multi-page PDF, and export PDF pages as images with a
  chosen DPI and page range
- Cancel a running batch, see per-file percentage progress, and get a taskbar
  alert when the batch finishes
- Batch conversion with one overall progress bar; a failed file does not stop
  the others
- Chinese / English UI, remembered between runs
- Light / dark / follow-system themes
- Engine status bar: built-in engines plus installed Office applications,
  Pandoc, Tesseract OCR and optional LibreOffice / Calibre are detected

## Supported conversions

| Source | Targets | Engine |
| --- | --- | --- |
| `jpg` `png` `webp` `avif` `bmp` `gif` `tiff` `ico` `ppm` | each other, plus `pdf` (quality setting for JPG/WEBP/AVIF) | Pillow + pillow-heif |
| `heic` | any of the formats above | Pillow + pillow-heif |
| `mp4` `mkv` `avi` `mov` `webm` `flv` `wmv` `m4v` `ts` `mpg` | `mp4` `mkv` `webm` `avi` `mov` `gif`, audio `mp3` `wav` `flac` `aac` `m4a` `ogg` `opus` `wma`, and `srt` subtitles | FFmpeg |
| `mp3` `wav` `flac` `aac` `m4a` `ogg` `opus` `wma` | each other | FFmpeg |
| `zip` `7z` `tar` `tar.gz` `tar.bz2` `tar.xz` | `zip` `7z` `tar` `tar.gz` `tar.xz` | stdlib + py7zr |
| `txt` `md` `html` | each other | Markdown, BeautifulSoup, markdownify |
| `csv` `xlsx` | each other | openpyxl |
| `docx` `doc` `odt` `rtf` | `pdf` | Microsoft Word (COM) or LibreOffice |
| `xlsx` `xls` | `pdf`; `xls` also to `xlsx` | Microsoft Excel (COM) or LibreOffice |
| `pptx` `ppt` | `pdf` | Microsoft PowerPoint (COM) or LibreOffice |
| `pdf` | `docx` (Word), `docx · Layout` (no Word needed), `docx · OCR` (scanned PDFs), `txt`, `png` / `jpg` (a ZIP of page images) | Word, pdfplumber, Tesseract, python-docx, pypdf, pypdfium2 |
| `docx` `odt` `rtf` `epub` `md` `html` `txt` | `md` `html` `txt` `docx` `odt` `rtf` `epub` (except the source format) | Pandoc |
| `epub` `mobi` `azw3` | `epub` `mobi` `azw3` `pdf` `txt` | Calibre |

Office conversions prefer the installed Microsoft Office (Word/Excel/PowerPoint)
and fall back to LibreOffice when Office is not available. Neither suite is
bundled in the slim build; the full build bundles LibreOffice. PDF page images
are rendered at about 144 DPI and delivered as one ZIP per PDF.

PDF → TXT automatically falls back to Tesseract OCR when a PDF has no text layer
(a scanned document). Chinese and English OCR data is bundled with the app; the
Tesseract program itself must be installed.

Video/audio conversions are re-encodes. A single file can be converted to
several formats at once; each format is an independent job. The audio and
subtitle track numbers in Settings apply globally to video files; the SRT
target only appears for videos that actually contain a subtitle stream.

## Download

Grab the latest release, unzip it anywhere and run
`FileFormatConverter.exe`. Two packages are published:

- **Slim** (~142 MB): FFmpeg and OCR language data bundled; Microsoft Office,
  LibreOffice, Pandoc, Tesseract and Calibre are detected if installed.
- **Full** (~2.4 GB unpacked, ~882 MB download; the bundled document tools
  alone are about 2.2 GB): also bundles LibreOffice, Pandoc, Tesseract and
  Calibre, so documents, OCR and e-books work on a fresh Windows computer
  without installing anything else. Microsoft Office itself cannot be bundled
  (licensing); exact PDF → Word reflow still needs Microsoft Word, while
  `DOCX · Layout` works without it.

Windows installers are also provided (`FileFormatConverter-*-Setup.exe`). They
let you choose the install folder, create Start Menu entries, and optionally
enable a desktop shortcut, an Explorer context-menu entry and Open with entries.
The default install is per-user and needs no administrator rights; the
installer can also run elevated to install under Program Files.
Unsigned installers may show the Windows SmartScreen prompt; choose
"More info → Run anyway". SHA-256 hashes are published in `SHA256SUMS.txt`.

Missing tools are greyed out automatically.

## Run from source

Requirements: Python 3.10+ (Windows, macOS or Linux).

```bash
git clone https://github.com/fwhhhh/file-format-converter.git
cd file-format-converter
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
python scripts/download_deps.py   # Windows: fetch FFmpeg into vendor/ffmpeg
python run.py
```

On macOS or Linux, install ffmpeg with `brew install ffmpeg` or
`sudo apt install ffmpeg` instead of running `download_deps.py`.

### Optional document tools

The app calls these tools when they are installed; the full build bundles them.

```bash
winget install JohnMacFarlane.Pandoc      # docx/odt/epub ↔ md/html/txt
winget install UB-Mannheim.TesseractOCR   # OCR for scanned PDFs
winget install TheDocumentFoundation.LibreOffice   # free Office fallback
winget install calibre.calibre            # epub / mobi / azw3
```

On macOS/Linux use `brew install pandoc tesseract libreoffice calibre` or the
equivalent package. The Chinese and English OCR language data is already
bundled in the project.

## Build a portable package

```bash
python scripts/make_icon.py
python scripts/build.py            # slim build
python scripts/build.py --full     # bundles LibreOffice, Pandoc, Tesseract, Calibre
```

The slim result is `dist/FileFormatConverter/`; the full result is
`dist/FileFormatConverter-Full/`. Zip either folder and it can be copied to
another Windows computer and started directly. The build script bundles
`vendor/ffmpeg`, the OCR language data, the license notices and the application
icon; the full build additionally bundles the document tools. Building the full
package requires those tools to be installed on the build machine.

### Build installers

```bash
winget install JRSoftware.InnoSetup
python scripts/build_installer.py --all
```

The generated setup files are written to `dist`. The installer supports a
selectable folder, an optional desktop shortcut and both Chinese and English
setup languages.

## Release automation

Pushing a tag such as `v0.6.1` runs the release workflow, builds the slim
package on a Windows runner and creates a GitHub Release. The full package is
built locally with `python scripts/build.py --full`, because it needs Microsoft
Office / LibreOffice / Pandoc / Tesseract / Calibre installed on the build
machine.

## Test

```bash
python -m pytest
```

The suite covers format sniffing, every engine, and a GUI smoke test with the
offscreen Qt platform.

To verify a built package on another machine, run:

```bash
FileFormatConverter.exe --selftest
```

It writes `selftest.txt` next to the executable with one line per conversion,
so you can confirm that Pillow, HEIC, 7z, openpyxl and FFmpeg all work there.

## Project layout

```
app/
  main.py            entry point
  i18n.py            Chinese / English strings
  settings.py        QSettings wrapper
  core/              detection, models, job scheduling, helpers
  engines/           office / libreoffice / pdf / pandoc / calibre / ocr / image / media / archive / text / table
  ui/                main window, file cards, dialogs, theme
scripts/             dependency download, icon, screenshots
tests/               pytest suite
vendor/              FFmpeg binaries (downloaded, not tracked by git)
```

## Verify downloads

`SHA256SUMS.txt` in the release folder contains the hashes of the ZIP and setup
files. On Windows:

```powershell
Get-FileHash .\FileFormatConverter-0.8.0-win64.zip -Algorithm SHA256
```

The installers are not code-signed. Removing the SmartScreen warning requires a
code-signing certificate (a paid OV/EV certificate, or a free open-source
signing service such as SignPath). A self-signed certificate does not help other
users.

## Known limitations

- Exact PDF → Word reflow uses Microsoft Word. The `DOCX · Layout` target
  rebuilds text-based PDFs with pdfplumber and does not need Word; it keeps
  page size, paragraphs, indents and approximate font sizes, but not images.
  Scanned PDFs can use the `DOCX · OCR` target instead.
- LibreOffice cannot reconstruct an editable Word file from a PDF; use
  `DOCX · Layout`, `DOCX · OCR` or Microsoft Word. Everything else works with
  the full build.
- The slim build requires Microsoft Office or LibreOffice for Office formats,
  Pandoc for Markdown conversions, Tesseract for OCR and Calibre for e-books.
- Audio and subtitle track numbers are global settings; conversions fail with a
  clear message when the selected track does not exist in a file.
- Bitmap subtitles (PGS/VobSub) cannot be exported as SRT.
- Password-protected archives are rejected.
- Password-protected PDFs are rejected by the PDF toolbox and PDF conversions.
- GIF output is a re-encoded animation; expect a larger file than a video.
- XLSX to CSV converts the active worksheet only.
- PDF → PNG / JPG returns one ZIP per PDF containing all pages; docx → Markdown
  may create a `<name>_media` folder for embedded images.
- Windows 11 lists the classic context-menu entry under "Show more options";
  the modern top-level menu requires a signed shell extension.

## License

MIT. FFmpeg is invoked as a separate executable and is distributed under the
LGPL; see [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md).
