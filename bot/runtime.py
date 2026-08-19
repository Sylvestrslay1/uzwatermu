from __future__ import annotations

import json
import os
import signal
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable


class AlreadyRunningError(RuntimeError):
    pass


class ProcessLock:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self._file = None

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        file = self.path.open("a+b")
        if file.tell() == 0:
            file.write(b"0")
            file.flush()
        file.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            file.close()
            raise AlreadyRunningError(
                "Botning boshqa nusxasi allaqachon ishlayapti."
            ) from error
        self._file = file
        self._write_owner()

    def _write_owner(self) -> None:
        if self._file is None:
            return
        payload = json.dumps(
            {
                "pid": os.getpid(),
                "started_at": datetime.now().isoformat(timespec="seconds"),
            }
        ).encode("utf-8")
        self._file.seek(1)
        self._file.truncate()
        self._file.write(payload)
        self._file.flush()

    def release(self) -> None:
        if self._file is None:
            return
        try:
            self._file.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._file.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._file.fileno(), fcntl.LOCK_UN)
        finally:
            self._file.close()
            self._file = None

    def __enter__(self) -> ProcessLock:
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def install_shutdown_handlers(
    stop_event: threading.Event,
    on_shutdown: Callable[[], None] | None = None,
) -> None:
    def request_shutdown(signum: int, _frame: object) -> None:
        if stop_event.is_set():
            return
        stop_event.set()
        if on_shutdown:
            on_shutdown()

    signal.signal(signal.SIGINT, request_shutdown)
    signal.signal(signal.SIGTERM, request_shutdown)
    if os.name == "nt" and hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, request_shutdown)


def write_health_status(
    path: str | Path,
    *,
    state: str,
    started_at: str,
    details: str = "",
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "state": state,
        "pid": os.getpid(),
        "started_at": started_at,
        "heartbeat_at": datetime.now().isoformat(timespec="seconds"),
        "details": details,
    }
    temporary = target.with_name(f".{target.name}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def health_worker(
    stop_event: threading.Event,
    path: str | Path,
    started_at: str,
    interval_seconds: float = 15,
) -> None:
    while not stop_event.is_set():
        write_health_status(
            path,
            state="running",
            started_at=started_at,
        )
        stop_event.wait(max(interval_seconds, 1))
