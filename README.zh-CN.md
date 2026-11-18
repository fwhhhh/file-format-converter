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
- Word / Excel / PowerPoint 文档通过本机已安装的 Microsoft Office 转换；PDF 可转 Word、文本或逐页图片
- Pandoc 负责 Markdown / HTML / 文本与 docx / odt / rtf / epub 互转；Tesseract OCR 读取扫描版 PDF
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
| `docx` `doc` `odt` `rtf` | `pdf` | Microsoft Word（COM） |
| `xlsx` `xls` | `pdf`；`xls` 还可转 `xlsx` | Microsoft Excel（COM） |
| `pptx` `ppt` | `pdf` | Microsoft PowerPoint（COM） |
| `pdf` | `docx`（Word）、`txt`、`png` / `jpg`（逐页图片打包为 ZIP） | Word、pypdf、pypdfium2 |
| `docx` `odt` `rtf` `epub` `md` `html` `txt` | `md` `html` `txt` `docx` `odt` `rtf` `epub`（除源格式外） | Pandoc |

Office 转换调用的是电脑上已安装的 Microsoft Office，程序不会打包 Office。PDF 转图片按约 144 DPI 渲染，每份 PDF 输出一个包含全部页面的 ZIP。基于 Office 的转换仅在 Windows 上可用，macOS / Linux 上会自动隐藏这些目标格式。

PDF 没有文字层（扫描件）时，PDF → TXT 会自动改用 Tesseract OCR。中英文 OCR 语言数据已随程序打包，Tesseract 程序本身需要安装。

音视频互转都是重新编码；同一个文件勾选多个格式时，每个格式是独立的任务。

## 下载

到 Releases 下载最新压缩包，解压后双击 `FileFormatConverter.exe` 即可。发布包内置 FFmpeg（LGPL 构建）和中英文 OCR 语言数据，音视频转换与 OCR 不需要额外数据文件。Word / Excel / PowerPoint 格式需要电脑上装有 Microsoft Office，Pandoc 系格式需要 Pandoc，OCR 需要 Tesseract；没装的引擎会自动灰显。

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

程序只调用已安装的工具，不会打包它们：

```bash
winget install JohnMacFarlane.Pandoc      # docx/odt/epub ↔ md/html/txt
winget install UB-Mannheim.TesseractOCR   # 扫描版 PDF 的 OCR
```

macOS / Linux 用 `brew install pandoc tesseract` 或对应包管理器安装。中英文 OCR 语言数据已放在项目的 `vendor/tessdata` 中。

## 打包成绿色版

```bash
python scripts/make_icon.py
python scripts/build.py
```

输出在 `dist/FileFormatConverter/`，整个文件夹压缩后拷到别的 Windows 电脑上即可直接运行。打包脚本会自动带上 `vendor/ffmpeg`、许可证说明和应用图标。

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
  engines/           Office / PDF / Pandoc / 图片 / 音视频 / 压缩包 / 文本 / 表格转换引擎
  ui/                主窗口、文件卡片、对话框、主题
scripts/             依赖下载、图标、截图脚本
tests/               pytest 测试
vendor/              FFmpeg 可执行文件（下载所得，不进入 git）
```

## 已知限制

- PDF → Word 使用 Word 的 PDF 重排功能：有文字层的数字化 PDF 效果好；扫描版 PDF 没有文字层，转 Word 只能得到页面图片（PDF → TXT 会自动走 OCR）。
- Office 转换要求本机安装 Microsoft Office，程序不会内置 Office；免费备选 LibreOffice 计划后续接入。
- Pandoc 系转换需要安装 Pandoc；OCR 需要安装 Tesseract。
- `epub` / `odt` / `rtf` 通过 Pandoc 支持；`mobi` / `azw3` 与 Calibre 转换尚未接入。
- 不支持加密压缩包。
- GIF 输出是重新编码的动画，体积会比视频大。
- XLSX 转 CSV 只转换当前工作表。
- PDF 转 PNG / JPG 每份 PDF 输出一个包含全部页面的 ZIP；docx 转 Markdown 可能生成 `<名称>_media` 文件夹存放内嵌图片。

## 开源协议

MIT。FFmpeg 以独立可执行文件的方式调用，遵循 LGPL；详见 [docs/THIRD_PARTY.md](docs/THIRD_PARTY.md)。
