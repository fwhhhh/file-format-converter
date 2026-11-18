"""Archive conversions: uncompress to a temporary folder, then repack."""

from __future__ import annotations

import shutil
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

from ..core.formats import ext_of_path
from .base import Engine, EngineError, Progress

ARCHIVE_SOURCES = {"zip", "7z", "tar", "tar.gz", "tar.bz2", "tar.xz"}
ARCHIVE_TARGETS = ["zip", "7z", "tar", "tar.gz", "tar.xz"]


def _has_py7zr() -> bool:
    try:
        import py7zr  # noqa: F401
    except Exception:
        return False
    return True


def _check_member_names(names: list[str]) -> None:
    for name in names:
        normalized = name.replace("\\", "/")
        pure = PurePosixPath(normalized)
        if pure.is_absolute() or ".." in pure.parts:
            raise EngineError(f"Unsafe path inside archive: {name}")
        if pure.parts and pure.parts[0].endswith(":"):
            raise EngineError(f"Unsafe path inside archive: {name}")


def _iter_files(root: Path):
    for path in sorted(root.rglob("*")):
        if path.is_file():
            yield path


class ArchiveEngine(Engine):
    key = "archive"
    label_key = "engine_archive"

    def available(self) -> bool:
        return True

    def targets(self, src_ext: str) -> list[str]:
        if src_ext not in ARCHIVE_SOURCES:
            return []
        result = [fmt for fmt in ARCHIVE_TARGETS if fmt != src_ext]
        if not _has_py7zr():
            result = [fmt for fmt in result if fmt != "7z"]
        return result

    def convert(
        self,
        src: Path,
        dst: Path,
        options: dict,
        progress: Progress | None = None,
    ) -> None:
        target = ext_of_path(dst)
        if target == "7z" and not _has_py7zr():
            raise EngineError("py7zr is required for 7z archives")
        temp_dir = Path(tempfile.mkdtemp(prefix="ffc_archive_"))
        try:
            if progress is not None:
                progress(0.05)
            self._extract(src, temp_dir)
            if progress is not None:
                progress(0.55)
            self._pack(temp_dir, dst, target)
            if progress is not None:
                progress(1.0)
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001
            raise EngineError(str(exc)) from exc
        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)

    # ------------------------------------------------------------- extract

    def _extract(self, src: Path, temp_dir: Path) -> None:
        ext = ext_of_path(src)
        if ext == "zip":
            self._extract_zip(src, temp_dir)
        elif ext == "7z":
            self._extract_7z(src, temp_dir)
        elif ext in ("tar", "tar.gz", "tar.bz2", "tar.xz"):
            self._extract_tar(src, temp_dir)
        else:
            raise EngineError(f"Unsupported archive: {ext}")

    def _extract_zip(self, src: Path, temp_dir: Path) -> None:
        try:
            with zipfile.ZipFile(src) as archive:
                infos = archive.infolist()
                if any(info.flag_bits & 0x1 for info in infos):
                    raise EngineError("Encrypted archives are not supported")
                _check_member_names([info.filename for info in infos])
                archive.extractall(temp_dir)
        except EngineError:
            raise
        except (zipfile.BadZipFile, RuntimeError, OSError) as exc:
            raise EngineError(str(exc)) from exc

    def _extract_7z(self, src: Path, temp_dir: Path) -> None:
        try:
            import py7zr
        except Exception as exc:
            raise EngineError("py7zr is required for 7z archives") from exc
        try:
            with py7zr.SevenZipFile(src, "r") as archive:
                _check_member_names(archive.getnames())
                archive.extractall(path=temp_dir)
        except EngineError:
            raise
        except Exception as exc:  # noqa: BLE001 - py7zr raises many types
            raise EngineError(str(exc)) from exc

    def _extract_tar(self, src: Path, temp_dir: Path) -> None:
        try:
            with tarfile.open(src, "r:*") as archive:
                members = archive.getmembers()
                _check_member_names([member.name for member in members])
                if any(member.issym() or member.islnk() for member in members):
                    raise EngineError("Archives with links are not supported")
                try:
                    archive.extractall(temp_dir, filter="data")
                except TypeError:
                    archive.extractall(temp_dir)
        except EngineError:
            raise
        except (tarfile.TarError, OSError) as exc:
            raise EngineError(str(exc)) from exc

    # ---------------------------------------------------------------- pack

    def _pack(self, temp_dir: Path, dst: Path, target: str) -> None:
        files = list(_iter_files(temp_dir))
        if target == "zip":
            with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED) as archive:
                for path in files:
                    archive.write(path, path.relative_to(temp_dir).as_posix())
            return
        if target == "7z":
            if not _has_py7zr():
                raise EngineError("py7zr is required for 7z archives")
            import py7zr

            with py7zr.SevenZipFile(dst, "w") as archive:
                for path in files:
                    archive.write(path, path.relative_to(temp_dir).as_posix())
            return
        if target in ("tar", "tar.gz", "tar.xz"):
            mode = {"tar": "w", "tar.gz": "w:gz", "tar.xz": "w:xz"}[target]
            with tarfile.open(dst, mode) as archive:
                for path in files:
                    archive.add(path, path.relative_to(temp_dir).as_posix())
            return
        raise EngineError(f"Unsupported archive target: {target}")
