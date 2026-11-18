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
| Pandoc (external) | GPL-2.0-or-later | Document conversion through a user-installed Pandoc |
| Tesseract OCR (external) | Apache-2.0 | OCR through a user-installed Tesseract |
| tessdata_fast data | Apache-2.0 | Bundled Chinese/English OCR language data |

Notes:

* FFmpeg is **not linked** into the application. It is invoked as a separate
  executable. The LGPL build distributed with release packages is downloaded
  from <https://github.com/BtbN/FFmpeg-Builds> and the corresponding source
  code is available from <https://ffmpeg.org/download.html>.
* Microsoft Office is **not redistributed**. Word, Excel and PowerPoint
  conversions only use the copy that is already installed on the user's
  computer, through COM automation.
* Pandoc and Tesseract are **not redistributed** either; the app invokes the
  copies installed by the user. Only the Apache-2.0 OCR language data
  (`tessdata_fast`) is bundled.
