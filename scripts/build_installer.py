"""Build Windows installers with Inno Setup.

Usage:
    python scripts/build_installer.py --all
    python scripts/build_installer.py --slim
    python scripts/build_installer.py --full

The slim and full application folders must already exist in ``dist`` (build
them with ``scripts/build.py`` first).  Installers are written to ``dist``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import __version__  # noqa: E402

VARIANTS = {
    "slim": {
        "source": ROOT / "dist" / "FileFormatConverter",
        "exe": "FileFormatConverter.exe",
        "app_name": "格式转换小工具",
        "app_id": "{{6C2E7A4D-3B1F-4D9E-8A5C-1F2B3C4D5E6F}",
        "default_dir": "FileFormatConverter",
        "output_base": f"FileFormatConverter-{__version__}-Setup",
        "compression": "lzma2/ultra64",
    },
    "full": {
        "source": ROOT / "dist" / "FileFormatConverter-Full",
        "exe": "FileFormatConverter-Full.exe",
        "app_name": "格式转换小工具（完整版）",
        "app_id": "{{9A1D4E7B-2C5F-4B8A-9D3E-6F1A2B3C4D5E}",
        "default_dir": "FileFormatConverter-Full",
        "output_base": f"FileFormatConverter-Full-{__version__}-Setup",
        "compression": "lzma2/fast",
    },
}

SUPPORTED_EXTS = [
    "jpg", "jpeg", "png", "webp", "avif", "bmp", "gif", "tif", "tiff", "ico",
    "heic", "ppm",
    "mp4", "mkv", "avi", "mov", "webm", "flv", "wmv", "m4v", "ts", "mpg",
    "mp3", "wav", "flac", "aac", "m4a", "ogg", "opus", "wma",
    "zip", "7z", "tar", "gz", "bz2", "xz",
    "txt", "md", "html", "csv", "xlsx",
    "docx", "doc", "odt", "rtf", "pptx", "ppt", "pdf", "epub", "mobi", "azw3",
]


def _registry_section(exe: str) -> str:
    app_exe = "{app}\\" + exe
    icon = '"' + app_exe + '"'
    command = '"""' + app_exe + '"" ""%1"""'
    background_command = '"""' + app_exe + '"" ""%V"""'
    label = '"用格式转换小工具转换 / Convert with File Format Converter"'
    supported_label = '"格式转换支持的文件 / Supported by File Format Converter"'
    lines = ["[Registry]"]
    for subkey, data in (
        (r"Software\Classes\*\shell\FileFormatConverter", label),
        (r"Software\Classes\Directory\shell\FileFormatConverter", label),
        (r"Software\Classes\Directory\Background\shell\FileFormatConverter", label),
    ):
        lines.append(
            f'Root: HKCU; Subkey: "{subkey}"; ValueType: string; '
            f'ValueName: ""; ValueData: {data}; Tasks: contextmenu; Flags: uninsdeletekey'
        )
        lines.append(
            f'Root: HKCU; Subkey: "{subkey}"; ValueType: string; '
            f'ValueName: "Icon"; ValueData: {icon}; Tasks: contextmenu; '
            f"Flags: uninsdeletekey"
        )
    for subkey, command_data in (
        (r"Software\Classes\*\shell\FileFormatConverter\command", command),
        (r"Software\Classes\Directory\shell\FileFormatConverter\command", command),
        (
            r"Software\Classes\Directory\Background\shell\FileFormatConverter\command",
            background_command,
        ),
    ):
        lines.append(
            f'Root: HKCU; Subkey: "{subkey}"; ValueType: string; '
            f'ValueName: ""; ValueData: {command_data}; Tasks: contextmenu; '
            f"Flags: uninsdeletekey"
        )

    lines.append(
        'Root: HKCU; Subkey: "Software\\Classes\\FileFormatConverter.File"; '
        f'ValueType: string; ValueName: ""; ValueData: {supported_label}; '
        "Tasks: openwith; Flags: uninsdeletekey"
    )
    lines.append(
        'Root: HKCU; Subkey: "Software\\Classes\\FileFormatConverter.File\\DefaultIcon"; '
        f'ValueType: string; ValueName: ""; ValueData: {icon}; '
        "Tasks: openwith; Flags: uninsdeletekey"
    )
    lines.append(
        'Root: HKCU; Subkey: "Software\\Classes\\FileFormatConverter.File\\shell\\open\\command"; '
        f'ValueType: string; ValueName: ""; ValueData: {command}; '
        "Tasks: openwith; Flags: uninsdeletekey"
    )
    for extension in SUPPORTED_EXTS:
        lines.append(
            f'Root: HKCU; Subkey: "Software\\Classes\\.{extension}\\OpenWithProgids"; '
            'ValueType: string; ValueName: "FileFormatConverter.File"; '
            'ValueData: ""; Tasks: openwith; Flags: uninsdeletevalue'
        )
    return "\n".join(lines) + "\n"


def find_iscc() -> Path | None:
    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Inno Setup 6" / "ISCC.exe",
        Path("C:/Program Files (x86)/Inno Setup 6/ISCC.exe"),
        Path("C:/Program Files/Inno Setup 6/ISCC.exe"),
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    from shutil import which

    found = which("iscc")
    return Path(found) if found else None


def build_script(variant: str, config: dict) -> Path:
    source: Path = config["source"]
    if not source.exists() or not (source / config["exe"]).exists():
        raise FileNotFoundError(
            f"Missing package folder: {source}\n"
            "Build it first with scripts/build.py"
            + (" --full" if variant == "full" else "")
        )
    build_dir = ROOT / "build" / "installer"
    build_dir.mkdir(parents=True, exist_ok=True)
    script_path = build_dir / f"{variant}.iss"
    chinese_isl = ROOT / "assets" / "installer" / "ChineseSimplified.isl"
    version_info = __version__ + (".0" if __version__.count(".") == 2 else "")
    registry_section = _registry_section(config["exe"])
    script = f"""; Generated by scripts/build_installer.py
[Setup]
AppId={config["app_id"]}
AppName={config["app_name"]}
AppVersion={__version__}
AppVerName={config["app_name"]} {__version__}
AppPublisher=fwh_hhh
AppPublisherURL=https://github.com/fwhhhh/file-format-converter
AppSupportURL=https://github.com/fwhhhh/file-format-converter
AppUpdatesURL=https://github.com/fwhhhh/file-format-converter
AppCopyright=MIT License
DefaultDirName={{autopf}}\\{config["default_dir"]}
DefaultGroupName={config["app_name"]}
DisableDirPage=no
DisableProgramGroupPage=yes
AllowNoIcons=yes
LicenseFile="{ROOT / "LICENSE"}"
OutputDir="{ROOT / "dist"}"
OutputBaseFilename={config["output_base"]}
SetupIconFile="{ROOT / "assets" / "app.ico"}"
UninstallDisplayIcon={{app}}\\{config["exe"]}
UninstallDisplayName={config["app_name"]} {__version__}
Compression={config["compression"]}
SolidCompression=yes
LZMAUseSeparateProcess=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog commandline
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
CloseApplications=yes
RestartApplications=no
ChangesAssociations=yes
SetupLogging=yes
VersionInfoVersion={version_info}
VersionInfoProductName={config["app_name"]}
VersionInfoCompany=fwh_hhh
VersionInfoDescription={config["app_name"]} installer

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "chinesesimplified"; MessagesFile: "{chinese_isl}"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式 / Create a desktop shortcut"; GroupDescription: "附加图标 / Additional icons:"; Flags: unchecked
Name: "contextmenu"; Description: "在文件/文件夹右键菜单中显示「转换」 / Add a context-menu entry"; GroupDescription: "资源管理器集成 / Explorer integration:"; Flags: unchecked
Name: "openwith"; Description: "在「打开方式」中添加快捷项 / Add to the Open with menu"; GroupDescription: "资源管理器集成 / Explorer integration:"; Flags: unchecked

{registry_section}
[Files]
Source: "{source}\\*"; DestDir: "{{app}}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{{group}}\\{config["app_name"]}"; Filename: "{{app}}\\{config["exe"]}"
Name: "{{group}}\\卸载 {config["app_name"]}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{config["app_name"]}"; Filename: "{{app}}\\{config["exe"]}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{config["exe"]}"; Description: "启动 / Launch {config["app_name"]}"; Flags: nowait postinstall skipifsilent
"""
    script_path.write_text(script, encoding="utf-8-sig")
    return script_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Inno Setup installers")
    parser.add_argument("--all", action="store_true", help="build slim and full")
    parser.add_argument("--slim", action="store_true", help="build slim installer")
    parser.add_argument("--full", action="store_true", help="build full installer")
    args = parser.parse_args()
    if not (args.all or args.slim or args.full):
        args.all = True

    iscc = find_iscc()
    if iscc is None:
        print("Inno Setup is not installed.")
        print("Install it with: winget install JRSoftware.InnoSetup")
        return 1

    selected = []
    if args.all or args.slim:
        selected.append("slim")
    if args.all or args.full:
        selected.append("full")

    for variant in selected:
        config = VARIANTS[variant]
        print(f"Building {variant} installer...")
        try:
            script_path = build_script(variant, config)
        except FileNotFoundError as exc:
            print(exc)
            return 1
        completed = subprocess.run(
            [str(iscc), str(script_path)],
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if completed.returncode != 0:
            print(f"ISCC failed for {variant} (exit {completed.returncode})")
            return completed.returncode
        output = ROOT / "dist" / f"{config['output_base']}.exe"
        if not output.exists():
            print(f"Installer output missing: {output}")
            return 1
        print(f"  {output}")
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
