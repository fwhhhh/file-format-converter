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

Notes:

* FFmpeg is **not linked** into the application. It is invoked as a separate
  executable. The LGPL build distributed with release packages is downloaded
  from <https://github.com/BtbN/FFmpeg-Builds> and the corresponding source
  code is available from <https://ffmpeg.org/download.html>.
