"""Text conversions between plain text, Markdown and HTML."""

from __future__ import annotations

import html as html_module
import re
from pathlib import Path

from .base import Engine, EngineError, Progress

TEXT_EXTS = {"txt", "md", "html"}

_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<style>
  body {{ font-family: system-ui, "Segoe UI", sans-serif; max-width: 820px;
         margin: 2.5em auto; padding: 0 1.2em; line-height: 1.65;
         color: #222; }}
  pre {{ background: #f5f5f5; padding: 0.8em; overflow: auto; border-radius: 4px; }}
  code {{ font-family: Consolas, "Courier New", monospace; }}
  table {{ border-collapse: collapse; }}
  th, td {{ border: 1px solid #ccc; padding: 4px 10px; }}
  blockquote {{ border-left: 3px solid #ccc; margin-left: 0; padding-left: 1em;
                color: #555; }}
</style>
</head>
<body>
{body}
</body>
</html>
"""


def _decode(data: bytes) -> str:
    for encoding in ("utf-8-sig", "gb18030", "latin-1"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _read_text(path: Path) -> str:
    return _decode(path.read_bytes())


def _txt_to_html(text: str) -> str:
    blocks = re.split(r"\r?\n\s*\r?\n", text.strip())
    parts = []
    for block in blocks:
        if not block.strip():
            continue
        escaped = html_module.escape(block).replace("\r\n", "\n").replace("\n", "<br>\n")
        parts.append(f"<p>{escaped}</p>")
    return "\n".join(parts)


def _clean_html(text: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style", "head", "title"]):
        tag.decompose()
    return str(soup)


def _html_to_text(text: str) -> str:
    from bs4 import BeautifulSoup

    soup = BeautifulSoup(_clean_html(text), "html.parser")
    raw = soup.get_text("\n")
    lines = [line.rstrip() for line in raw.splitlines()]
    collapsed: list[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if blank:
                continue
            blank = True
            collapsed.append("")
        else:
            blank = False
            collapsed.append(line)
    return "\n".join(collapsed).strip() + "\n"


def _md_to_html(text: str) -> str:
    import markdown

    return markdown.markdown(
        text,
        extensions=["extra", "tables", "fenced_code", "sane_lists"],
    )


def _html_to_md(text: str) -> str:
    from markdownify import markdownify

    result = markdownify(_clean_html(text), heading_style="ATX")
    return re.sub(r"\n{3,}", "\n\n", result).strip() + "\n"


class TextEngine(Engine):
    key = "text"
    label_key = "engine_text"

    def available(self) -> bool:
        try:
            import bs4  # noqa: F401
            import markdown  # noqa: F401
            import markdownify  # noqa: F401
        except Exception:
            return False
        return True

    def targets(self, src_ext: str) -> list[str]:
        if src_ext not in TEXT_EXTS:
            return []
        return [fmt for fmt in ("html", "md", "txt") if fmt != src_ext]

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        source_ext = src.suffix.lower().lstrip(".")
        target = dst.suffix.lower().lstrip(".")
        text = _read_text(src)
        try:
            if target == "html":
                if source_ext == "md":
                    body = _md_to_html(text)
                elif source_ext == "txt":
                    body = _txt_to_html(text)
                else:
                    body = text
                result = _HTML_TEMPLATE.format(
                    title=html_module.escape(src.stem),
                    body=body,
                )
            elif target == "md":
                if source_ext == "html":
                    result = _html_to_md(text)
                elif source_ext == "txt":
                    result = text
                else:
                    raise EngineError("Markdown to Markdown is not supported")
            elif target == "txt":
                if source_ext == "md":
                    result = _html_to_text(_md_to_html(text))
                elif source_ext == "html":
                    result = _html_to_text(text)
                else:
                    result = text
            else:
                raise EngineError(f"Unsupported text target: {target}")
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        dst.write_text(result, encoding="utf-8")
        if progress is not None:
            progress(1.0)
