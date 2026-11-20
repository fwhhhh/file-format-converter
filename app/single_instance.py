"""Forward files opened from Explorer to the already running window."""

from __future__ import annotations

import json
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QLockFile, QObject, Signal
from PySide6.QtNetwork import QLocalServer, QLocalSocket

SERVER_NAME = "FileFormatConverter-single-instance"
LOCK_PATH = Path(tempfile.gettempdir()) / "FileFormatConverter-single-instance.lock"


class SingleInstance(QObject):
    """A tiny local-socket server used to reuse the first window.

    Windows starts a separate process for every file selected in a context
    menu.  The second process sends its paths to the first one and exits, so a
    multi-file selection still lands in one batch.
    """

    paths_received = Signal(list)

    def __init__(self, name: str = SERVER_NAME) -> None:
        super().__init__()
        self.name = name
        self.server: QLocalServer | None = None
        self.buffers: dict[int, tuple[QLocalSocket, bytearray]] = {}
        self.lock: QLockFile | None = None

    def acquire(self) -> bool:
        """Claim the single-instance lock for this user."""
        self.lock = QLockFile(str(LOCK_PATH))
        return self.lock.tryLock(0)

    def notify_running(self, paths: list[str], wait: float = 1.5) -> bool:
        """Send paths to the running instance.  False means none is running.

        If another process is still starting, keep trying for ``wait`` seconds
        so a multi-file Explorer selection does not spawn several windows.
        """
        deadline = time.monotonic() + wait
        while True:
            socket = QLocalSocket()
            socket.connectToServer(self.name)
            if socket.waitForConnected(200):
                payload = json.dumps({"paths": paths}, ensure_ascii=False)
                socket.write(payload.encode("utf-8") + b"\n")
                socket.flush()
                socket.waitForBytesWritten(500)
                # The server acknowledges after reading the line, so the
                # second process does not exit before the first has the paths.
                socket.waitForReadyRead(3000)
                socket.disconnectFromServer()
                return True
            socket.abort()
            if time.monotonic() >= deadline:
                return False
            time.sleep(0.05)

    def listen(self, takeover: bool = True) -> bool:
        server = QLocalServer(self)
        server.newConnection.connect(self._accept)
        if server.listen(self.name):
            self.server = server
            return True
        if not takeover:
            server.deleteLater()
            return False
        # A stale socket may be left after a crash; remove and retry once.
        QLocalServer.removeServer(self.name)
        if server.listen(self.name):
            self.server = server
            return True
        server.deleteLater()
        return False

    def close(self) -> None:
        for socket, _buffer in list(self.buffers.values()):
            try:
                socket.disconnectFromServer()
                socket.deleteLater()
            except RuntimeError:
                pass
        self.buffers.clear()
        if self.server is not None:
            self.server.close()
            self.server.deleteLater()
            self.server = None
            QLocalServer.removeServer(self.name)
        if self.lock is not None:
            if self.lock.isLocked():
                self.lock.unlock()
            self.lock = None

    def _accept(self) -> None:
        while self.server is not None and self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            if socket is None:
                continue
            self.buffers[id(socket)] = (socket, bytearray())
            socket.readyRead.connect(lambda s=socket: self._read(s))
            socket.disconnected.connect(lambda s=socket: self._finish(s))
            self._read(socket)

    def _read(self, socket: QLocalSocket) -> None:
        entry = self.buffers.get(id(socket))
        if entry is None:
            return
        buffer = entry[1]
        try:
            buffer.extend(bytes(socket.readAll()))
        except RuntimeError:
            return
        while b"\n" in buffer:
            line, _, rest = buffer.partition(b"\n")
            buffer[:] = rest
            self._dispatch(bytes(line))
            try:
                socket.write(b"ok\n")
                socket.flush()
            except RuntimeError:
                pass

    def _finish(self, socket: QLocalSocket) -> None:
        if id(socket) in self.buffers:
            self._read(socket)
        entry = self.buffers.pop(id(socket), None)
        if entry is not None and entry[1]:
            self._dispatch(bytes(entry[1]))
        try:
            socket.deleteLater()
        except RuntimeError:
            pass

    def _dispatch(self, data: bytes) -> None:
        if not data:
            return
        try:
            message = json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return
        raw_paths = message.get("paths") if isinstance(message, dict) else None
        if not isinstance(raw_paths, list):
            return
        paths = [str(Path(path)) for path in raw_paths if str(path).strip()]
        self.paths_received.emit(paths)
