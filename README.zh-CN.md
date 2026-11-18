# 格式转换小工具

[English](README.md)

一个极简的拖拽式文件格式转换工具。把文件或整个文件夹拖进窗口，勾选要转出的格式，点开始转换即可。一个文件可以同时转出多种格式，也可以一次转换多个文件。

![截图](docs/screenshot-zh.png)

## 功能

- 窗口任意位置都能拖入文件或文件夹
- 每个文件一张可折叠卡片，目标格式以圆角标签展示
- 支持多选目标格式：`photo.jpg` 勾选 `PNG` 和 `PDF`，会同时得到两个文件
- 按文件头识别真实格式，改了后缀的文件也能正确转换
- 转换完成后显示产物图标、实际大小，并可一键打开所在文件夹
- Word / Excel / PowerPoint 文档优先通过本机 Microsoft Office 转换，没有 Office 时用 LibreOffice 兜底；PDF 可转 Word、文本或逐页图片
- Pandoc 负责 Markdown / HTML / 文本与 docx / odt / rtf / epub 互转；Tesseract OCR 可把扫描版 PDF 识别为文本或可编辑的 Word；Calibre 转换电子书
- 可在设置里为输出文件名添加后缀
- PDF 工具箱：合并 PDF、按页或每 N 页拆分、提取页码范围、把多张图片合成多页 PDF、按指定 DPI 和页码范围把 PDF 导出为图片
- 转换中可取消，每个文件单独显示百分比，完成后有任务栏提醒
- 批量转换只有一个总进度条；某个文件失败不影响其它文件
- 中文 / English 界面，记住上次选择
- 浅色 / 深色 / 跟随系统三种主题
- 底部引擎状态：内置引擎、已安装的 Office 组件、Pandoc、Tesseract OCR，以及可选的 LibreOffice / Calibre 都会检测并显示

## 支持的转换

| 源格式 | 目标格式 | 引擎 |
| --- | --- | --- |
| `jpg` `png` `webp` `bmp` `gif` `tiff` `ico` `ppm` | 互相转换，另可转 `pdf`（JPG/WEBP 可调质量） | Pillow + pillow-heif |
| `heic` | 上述任意格式 | Pillow + pillow-heif |
| `mp4` `mkv` `avi` `mov` `webm` `flv` `wmv` `m4v` `ts` `mpg` | `mp4` `mkv` `webm` `avi` `mov` `gif`，以及音频 `mp3` `wav` `flac` `aac` `m4a` `ogg` `opus` `wma` | FFmpeg |
| `mp3` `wav` `flac` `aac` `m4a` `ogg` `opus` `wma` | 互相转换 | FFmpeg |
| `zip` `7z` `tar` `tar.gz` `tar.bz2` `tar.xz` | `zip` `7z` `tar` `tar.gz` `tar.xz` | 标准库 + py7zr |
| `txt` `md` `html` | 互相转换 | Markdown、BeautifulSoup、markdownify |
| `csv` `xlsx` | 互相转换 | openpyxl |
| `docx` `doc` `odt` `rtf` | `pdf` | Microsoft Word（COM）或 LibreOffice |
| `xlsx` `xls` | `pdf`；`xls` 还可转 `xlsx` | Microsoft Excel（COM）或 LibreOffice |
| `pptx` `ppt` | `pdf` | Microsoft PowerPoint（COM）或 LibreOffice |
| `pdf` | `docx`（Word）、`docx · OCR`（扫描件）、`txt`、`png` / `jpg`（逐页图片打包为 ZIP） | Word、Tesseract、python-docx、pypdf、pypdfium2 |
| `docx` `odt` `rtf` `epub` `md` `html` `txt` | `md` `html` `txt` `docx` `odt` `rtf` `epub`（除源格式外） | Pandoc |
| `epub` `mobi` `azw3` | `epub` `mobi` `azw3` `pdf` `txt` | Calibre |

Office 转换优先使用本机已安装的 Microsoft Office（Word/Excel/PowerPoint），没有 Office 时自动改用 LibreOffice。精简版不打包这两套软件，全内置版自带 LibreOffice。PDF 转图片按约 144 DPI 渲染，每份 PDF 输出一个包含全部页面的 ZIP。

PDF 没有文字层（扫描件）时，PDF → TXT 会自动改用 Tesseract OCR。中英文 OCR 语言数据已随程序打包，Tesseract 程序本身需要安装。

音视频互转都是重新编码；同一个文件勾选多个格式时，每个格式是独立的任务。

## 下载

到 Releases 下载最新压缩包，解压后双击 `FileFormatConverter.exe` 即可。发布分两个版本：

- **精简版**（约 138MB）：内置 FFmpeg 和 OCR 语言数据；Microsoft Office、LibreOffice、Pandoc、Tesseract、Calibre 装了就能用，没装时灰显。
- **全内置版**（解压约 2.4GB，下载约 914MB；其中文档工具本身约 2.1GB）：额外打包 LibreOffice、Pandoc、Tesseract 与 Calibre，换一台全新 Windows 电脑也能直接处理文档、OCR 和电子书。Microsoft Office 受授权限制不能打包；PDF → Word 仍需要本机安装 Word。

缺少的引擎会自动灰显。

## 从源码运行

需要 Python 3.10+（Windows / macOS / Linux）。

```bash
git clone https://github.com/fwhhhh/file-format-converter.git
cd file-format-converter
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements-dev.txt
python scripts/download_deps.py   # 仅 Windows：下载 FFmpeg 到 vendor/ffmpeg
python run.py
```

macOS / Linux 用户请用 `brew install ffmpeg` 或 `sudo apt install ffmpeg` 安装 FFmpeg，无需运行下载脚本。

### 可选文档工具

程序只调用已安装的工具，全内置版会把它们一起打包：

```bash
winget install JohnMacFarlane.Pandoc      # docx/odt/epub ↔ md/html/txt
winget install UB-Mannheim.TesseractOCR   # 扫描版 PDF 的 OCR
winget install TheDocumentFoundation.LibreOffice   # 免费的 Office 兜底
winget install calibre.calibre            # epub / mobi / azw3
```

macOS / Linux 用 `brew install pandoc tesseract libreoffice calibre` 或对应包管理器安装。中英文 OCR 语言数据已放在项目的 `vendor/tessdata` 中。

## 打包成绿色版

```bash
python scripts/make_icon.py
python scripts/build.py            # 精简版
python scripts/build.py --full     # 内置 LibreOffice、Pandoc、Tesseract、Calibre
```

精简版输出在 `dist/FileFormatConverter/`，全内置版输出在
`dist/FileFormatConverter-Full/`。整个文件夹压缩后拷到别的 Windows 电脑上即可直接运行。打包脚本会自动带上 `vendor/ffmpeg`、OCR 语言数据、许可证说明和应用图标；全内置版还会带上文档工具，因此打包机需要先装好这些工具。

## 测试

```bash
python -m pytest
```

测试覆盖格式识别、全部转换引擎，以及使用离屏 Qt 平台的界面冒烟测试。

验证打包后的程序是否在别的电脑上可用：

```bash
FileFormatConverter.exe --selftest
```

它会在 exe 旁边生成 `selftest.txt`，逐个列出转换结果，可确认 Pillow、HEIC、7z、openpyxl 与 FFmpeg 均正常。

## 目录结构

```
app/
  main.py            入口
  i18n.py            中英文案
  settings.py        QSettings 封装
  core/              格式识别、数据模型、任务调度、工具函数
  engines/           Office / LibreOffice / PDF / Pandoc / Calibre / OCR / 图片 / 音视频 / 压缩包 / 文本 / 表格转换引擎
  ui/                主窗口、文件卡片、对话框、主题
scripts/             依赖下载、图标、截图脚本
tests/               pytest 测试
vendor/              FFmpeg 可执行文件（下载所得，不进入 git）
```

## 已知限制

- PDF → Word 使用 Word 的 PDF 重排功能。扫描版 PDF 可以选择 `DOCX · OCR` 目标，得到可编辑的文字版 Word；页面排版和图片不会还原。
- PDF → Word 仍然需要本机安装 Microsoft Word；LibreOffice 无法把 PDF 还原成可编辑的 Word。其它文档转换在全内置版里不需要额外安装。
- 精简版的 Office 格式需要 Microsoft Office 或 LibreOffice，Markdown 转换需要 Pandoc，OCR 需要 Tesseract，电子书需要 Calibre。
- 不支持加密压缩包。
- PDF 工具箱和 PDF 转换不支持加密 PDF。
- GIF 输出是重新编码的动画，体积会比视频大。
- XLSX 转 CSV 只转换当前工作表。
- PDF 转 PNG / JPG 每份 PDF 输出一个包含全部页面的 ZIP；docx 转 Markdown 可能生成 `<名称>_media` 文件夹存放内嵌图片。

## 开源协议

MIT。FFmpeg 以独立可执行文件的方式调用，遵循 LGPL；详见 [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md)。
