"""Small bilingual (Chinese / English) string table.

The active language is a module level state.  The UI calls ``tr`` whenever it
needs a string, and calls ``retranslate`` on every widget after the language
changes.
"""

from __future__ import annotations

_LANGUAGE = "zh"
_LANGUAGES = ("zh", "en")

_STRINGS: dict[str, dict[str, str]] = {
    "app_title": {"zh": "格式转换小工具", "en": "File Format Converter"},
    "add_files": {"zh": "添加文件", "en": "Add files"},
    "add_folder": {"zh": "添加文件夹", "en": "Add folder"},
    "clear": {"zh": "清空", "en": "Clear"},
    "settings": {"zh": "设置", "en": "Settings"},
    "about": {"zh": "关于", "en": "About"},
    "remove": {"zh": "移除", "en": "Remove"},
    "drop_hint": {
        "zh": "把文件或文件夹拖到这里",
        "en": "Drop files or folders here",
    },
    "files_title": {"zh": "文件 · {n}", "en": "Files · {n}"},
    "files_empty": {"zh": "文件", "en": "Files"},
    "empty_right": {
        "zh": "拖入文件后，在这里勾选要转出的格式",
        "en": "Drop files, then pick the output formats here",
    },
    "targets": {"zh": "转出格式：", "en": "Convert to:"},
    "selected_one": {"zh": "已选 {n} 种格式", "en": "{n} format selected"},
    "selected_many": {"zh": "已选 {n} 种格式", "en": "{n} formats selected"},
    "apply_same": {"zh": "应用到同类文件", "en": "Apply to same type"},
    "start": {"zh": "开始转换", "en": "Start"},
    "converting": {"zh": "转换中…", "en": "Converting…"},
    "waiting": {"zh": "等待中", "en": "Waiting"},
    "failed": {"zh": "失败", "en": "Failed"},
    "result": {"zh": "转换结果：", "en": "Results:"},
    "summary": {
        "zh": "转换结束：成功 {ok} 个，失败 {fail} 个",
        "en": "Finished: {ok} succeeded, {fail} failed",
    },
    "added_one": {"zh": "已添加 {n} 个文件", "en": "Added {n} file"},
    "added_many": {"zh": "已添加 {n} 个文件", "en": "Added {n} files"},
    "skipped_one": {
        "zh": "已跳过 {n} 个不支持的文件",
        "en": "Skipped {n} unsupported file",
    },
    "skipped_many": {
        "zh": "已跳过 {n} 个不支持的文件",
        "en": "Skipped {n} unsupported files",
    },
    "duplicate_skipped_one": {
        "zh": "已跳过 {n} 个重复文件",
        "en": "Skipped {n} duplicate file",
    },
    "duplicate_skipped_many": {
        "zh": "已跳过 {n} 个重复文件",
        "en": "Skipped {n} duplicate files",
    },
    "unsupported_title": {"zh": "不支持的文件", "en": "Unsupported files"},
    "unsupported_body": {
        "zh": "以下文件无法识别或暂不支持：\n{names}",
        "en": "These files are not recognized or not supported yet:\n{names}",
    },
    "no_files_title": {"zh": "还没有文件", "en": "No files"},
    "no_files_body": {
        "zh": "请先把文件或文件夹拖进窗口，或使用「添加文件」。",
        "en": "Add or drop files first.",
    },
    "no_selection_title": {"zh": "没有勾选格式", "en": "No format selected"},
    "no_selection_body": {
        "zh": "请至少为一个文件勾选一种目标格式。",
        "en": "Select at least one target format.",
    },
    "output_title": {"zh": "选择保存位置", "en": "Choose output location"},
    "output_same": {"zh": "与源文件同一目录", "en": "Same folder as source"},
    "output_custom": {"zh": "自定义目录", "en": "Custom folder"},
    "browse": {"zh": "浏览…", "en": "Browse…"},
    "ok": {"zh": "确定", "en": "OK"},
    "cancel": {"zh": "取消", "en": "Cancel"},
    "close": {"zh": "关闭", "en": "Close"},
    "open": {"zh": "打开位置", "en": "Open"},
    "open_folder": {"zh": "打开所在文件夹", "en": "Open folder"},
    "custom_dir_invalid": {
        "zh": "自定义目录不可用：{path}",
        "en": "Custom folder is not usable: {path}",
    },
    "custom_dir_create_failed": {
        "zh": "无法创建目录：{path}",
        "en": "Cannot create folder: {path}",
    },
    "settings_title": {"zh": "设置", "en": "Settings"},
    "quality": {"zh": "图片质量（JPG / WEBP）", "en": "Image quality (JPG / WEBP)"},
    "preset": {"zh": "视频预设", "en": "Video preset"},
    "preset_high": {"zh": "高画质", "en": "High quality"},
    "preset_balanced": {"zh": "均衡", "en": "Balanced"},
    "preset_small": {"zh": "小体积", "en": "Small size"},
    "language": {"zh": "语言 / Language", "en": "Language / 语言"},
    "theme": {"zh": "外观", "en": "Appearance"},
    "theme_system": {"zh": "跟随系统", "en": "Follow system"},
    "theme_light": {"zh": "浅色", "en": "Light"},
    "theme_dark": {"zh": "深色", "en": "Dark"},
    "engines_title": {"zh": "引擎状态", "en": "Engine status"},
    "engine_available": {"zh": "可用", "en": "available"},
    "engine_missing": {"zh": "未安装", "en": "not installed"},
    "engine_image": {"zh": "图片（Pillow）", "en": "Images (Pillow)"},
    "engine_media": {"zh": "音视频（FFmpeg）", "en": "Audio / video (FFmpeg)"},
    "engine_archive": {"zh": "压缩包（7-Zip / 标准库）", "en": "Archives (7-Zip / stdlib)"},
    "engine_text": {
        "zh": "文本（Markdown / BeautifulSoup）",
        "en": "Text (Markdown / BeautifulSoup)",
    },
    "engine_table": {"zh": "表格（openpyxl）", "en": "Spreadsheets (openpyxl)"},
    "engine_pdf": {"zh": "PDF（pypdfium2 / pypdf）", "en": "PDF (pypdfium2 / pypdf)"},
    "engine_office": {
        "zh": "Office（Word / Excel / PowerPoint）",
        "en": "Office (Word / Excel / PowerPoint)",
    },
    "engine_word": {"zh": "Microsoft Word（Office）", "en": "Microsoft Word (Office)"},
    "engine_excel": {"zh": "Microsoft Excel（Office）", "en": "Microsoft Excel (Office)"},
    "engine_powerpoint": {
        "zh": "Microsoft PowerPoint（Office）",
        "en": "Microsoft PowerPoint (Office)",
    },
    "engine_pandoc": {"zh": "文档互转（Pandoc）", "en": "Documents (Pandoc)"},
    "engine_ocr": {"zh": "OCR 扫描识别（Tesseract）", "en": "OCR (Tesseract)"},
    "engine_libreoffice": {
        "zh": "办公文档（LibreOffice，可选）",
        "en": "Office documents (LibreOffice, optional)",
    },
    "engine_calibre": {"zh": "电子书（Calibre，可选）", "en": "E-books (Calibre, optional)"},
    "engine_hint_missing": {
        "zh": "未检测到：安装后重启本程序即可自动启用。",
        "en": "Not detected. Install it and restart this app to enable it.",
    },
    "engine_future_note": {
        "zh": "可选引擎未安装时会灰显。全内置版已包含 Pandoc、Tesseract、LibreOffice 与 Calibre。",
        "en": "Missing optional engines are greyed out. The full build bundles Pandoc, "
              "Tesseract, LibreOffice and Calibre.",
    },
    "download": {"zh": "下载安装", "en": "Download"},
    "engine_pill": {
        "zh": "引擎 {ok}/{total} 可用",
        "en": "Engines {ok}/{total} available",
    },
    "engine_status_tip": {
        "zh": "点击查看各转换引擎的安装状态",
        "en": "Click to see engine installation status",
    },
    "error_missing_engine": {
        "zh": "缺少转换引擎",
        "en": "Conversion engine is missing",
    },
    "image_info": {"zh": "{w}×{h} · {size}", "en": "{w}×{h} · {size}"},
    "media_info": {"zh": "{duration} · {size}", "en": "{duration} · {size}"},
    "pdf_info": {"zh": "{pages} 页 · {size}", "en": "{pages} pages · {size}"},
    "preparing": {"zh": "准备中…", "en": "Preparing…"},
    "ready": {"zh": "就绪", "en": "Ready"},
    "pdf_dpi": {"zh": "PDF 图片分辨率", "en": "PDF image DPI"},
    "pdf_tools": {"zh": "PDF 工具", "en": "PDF tools"},
    "pdf_merge": {"zh": "合并 PDF", "en": "Merge PDFs"},
    "pdf_split": {"zh": "拆分 PDF", "en": "Split PDF"},
    "pdf_extract": {"zh": "提取页面", "en": "Extract pages"},
    "pdf_images_to_pdf": {"zh": "图片 → 多页 PDF", "en": "Images → multi-page PDF"},
    "pdf_to_images": {"zh": "PDF → 图片", "en": "PDF → images"},
    "pdf_files": {"zh": "PDF 文件：", "en": "PDF files:"},
    "image_files": {"zh": "图片文件：", "en": "Images:"},
    "add": {"zh": "添加", "en": "Add"},
    "move_up": {"zh": "上移", "en": "Move up"},
    "move_down": {"zh": "下移", "en": "Move down"},
    "source_pdf": {"zh": "源 PDF：", "en": "Source PDF:"},
    "output_pdf": {"zh": "输出 PDF：", "en": "Output PDF:"},
    "output_folder": {"zh": "输出目录：", "en": "Output folder:"},
    "output_zip": {"zh": "输出 ZIP：", "en": "Output ZIP:"},
    "split_mode": {"zh": "拆分方式", "en": "Split mode"},
    "split_per_page": {"zh": "每页一个文件", "en": "One file per page"},
    "split_every": {"zh": "每 N 页一个文件", "en": "One file every N pages"},
    "pages_per_file": {"zh": "每份页数", "en": "Pages per file"},
    "page_range": {"zh": "页面范围", "en": "Page range"},
    "page_range_hint": {
        "zh": "留空表示全部，例如 1-3,5,8-10",
        "en": "Empty means all, e.g. 1-3,5,8-10",
    },
    "image_format": {"zh": "图片格式", "en": "Image format"},
    "choose_pdfs": {"zh": "选择 PDF", "en": "Choose PDFs"},
    "choose_images": {"zh": "选择图片", "en": "Choose images"},
    "merge_need_two": {"zh": "至少添加两个 PDF 文件", "en": "Add at least two PDF files"},
    "no_input": {"zh": "请选择输入文件", "en": "Choose an input file"},
    "no_output": {"zh": "请选择输出位置", "en": "Choose an output location"},
    "pdf_tool_error": {"zh": "操作失败", "en": "Operation failed"},
    "merged_done": {
        "zh": "已合并 {n} 页：\n{path}",
        "en": "Merged {n} pages:\n{path}",
    },
    "extracted_done": {
        "zh": "已提取 {n} 页：\n{path}",
        "en": "Extracted {n} pages:\n{path}",
    },
    "split_done": {
        "zh": "已拆分出 {n} 个文件：\n{path}",
        "en": "Split into {n} files:\n{path}",
    },
    "images_pdf_done": {
        "zh": "已生成 {n} 页 PDF：\n{path}",
        "en": "Created a {n}-page PDF:\n{path}",
    },
    "images_zip_done": {
        "zh": "已导出 {n} 张图片：\n{path}",
        "en": "Exported {n} images:\n{path}",
    },
    "cancel_conversion": {"zh": "取消转换", "en": "Cancel"},
    "cancelling": {"zh": "正在取消…", "en": "Cancelling…"},
    "cancelled_label": {"zh": "已取消", "en": "Cancelled"},
    "summary_cancelled": {
        "zh": "转换结束：成功 {ok} 个，失败 {fail} 个，取消 {cancelled} 个",
        "en": "Finished: {ok} succeeded, {fail} failed, {cancelled} cancelled",
    },
    "quit_title": {"zh": "正在转换", "en": "Conversion in progress"},
    "quit_body": {
        "zh": "还有转换任务正在进行。退出会等待当前任务完成，确定退出吗？",
        "en": "Some conversions are still running. Quitting will wait for them "
              "to finish. Quit anyway?",
    },
    "github_label": {"zh": "GitHub", "en": "GitHub"},
    "email_label": {"zh": "邮箱", "en": "Email"},
    "about_text": {
        "zh": (
            "图片、音视频、压缩包、文本、表格的自由转换。\n"
            "基于 PySide6、Pillow 与 FFmpeg。\n\n"
            "MIT License"
        ),
        "en": (
            "Convert images, audio/video, archives, text and spreadsheets.\n"
            "Built with PySide6, Pillow and FFmpeg.\n\n"
            "MIT License"
        ),
    },
}


def set_language(lang: str) -> None:
    global _LANGUAGE
    if lang in _LANGUAGES:
        _LANGUAGE = lang


def language() -> str:
    return _LANGUAGE


def tr(key: str, **kwargs: object) -> str:
    entry = _STRINGS.get(key)
    if entry is None:
        return key
    text = entry.get(_LANGUAGE) or entry.get("en") or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text


def trn(one_key: str, many_key: str, n: int, **kwargs: object) -> str:
    """Translate a count with simple English pluralisation."""
    key = one_key if n == 1 else many_key
    return tr(key, n=n, **kwargs)
