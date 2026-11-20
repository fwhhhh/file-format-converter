# Third-party components

This project bundles or depends on the following open-source components.

| Component | License | Usage |
| --- | --- | --- |
| PySide6 (Qt for Python) | LGPL-3.0 | GUI framework |
| Pillow | MIT-CMU | Image reading/writing |
| pillow-heif | BSD-3-Clause | HEIC/HEIF support |
| FFmpeg (LGPL build by BtbN) | LGPL-2.1-or-later | Audio/video conversion (external executable) |
| py7zr | LGPL-2.1-or-later | 7z archives |
| openpyxl | MIT | XLSX reading/writing |
| Markdown | BSD-3-Clause | Markdown to HTML |
| BeautifulSoup | MIT | HTML to text |
| markdownify | MIT | HTML to Markdown |
| pywin32 | PSF-2.0 | Microsoft Office automation (COM) |
| pypdfium2 | BSD-3-Clause AND Apache-2.0 | PDF page rendering |
| pypdf | BSD-3-Clause | PDF text extraction |
| pdfplumber | MIT | PDF layout reconstruction for Word |
| pdfminer.six | MIT | PDF parsing used by pdfplumber |
| cryptography | Apache-2.0 OR BSD-3-Clause | PDF encryption support used by pdfplumber |
| python-docx | MIT | OCR Word document output |
| lxml | BSD-3-Clause | XML handling used by python-docx |
| Pandoc (external in slim, bundled in full) | GPL-2.0-or-later | Document conversion |
| Tesseract OCR (external in slim, bundled in full) | Apache-2.0 | OCR |
| LibreOffice (external in slim, bundled in full) | MPL-2.0 | Office document fallback |
| Calibre (external in slim, bundled in full) | GPL-3.0 | E-book conversion |
| tessdata_fast data | Apache-2.0 | Bundled Chinese/English OCR language data |
| Inno Setup (build-time) | Inno Setup License | Windows installers |
| ChineseSimplified.isl | Inno Setup License | Chinese installer UI |

Notes:

* FFmpeg is **not linked** into the application. It is invoked as a separate
  executable. The LGPL build distributed with release packages is downloaded
  from <https://github.com/BtbN/FFmpeg-Builds> and the corresponding source
  code is available from <https://ffmpeg.org/download.html>.
* Microsoft Office is **not redistributed**. Word, Excel and PowerPoint
  conversions only use the copy that is already installed on the user's
  computer, through COM automation.
* The **full** build redistributes Pandoc (GPL-2.0-or-later), Tesseract
  (Apache-2.0), LibreOffice (MPL-2.0) and Calibre (GPL-3.0) as separate
  executables. Their source code and license texts are available from
  <https://pandoc.org>, <https://github.com/tesseract-ocr/tesseract>,
  <https://www.libreoffice.org/about-us/licenses/> and
  <https://calibre-ebook.com/about>. The slim build only invokes copies that
  the user installed.
* The Apache-2.0 OCR language data (`tessdata_fast`) is bundled in both builds.
