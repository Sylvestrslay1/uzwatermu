from __future__ import annotations

import logging
import os
import signal
import subprocess
import sys
import threading
import time
from logging.handlers import RotatingFileHandler
from pathlib import Path

from tools.windows_job import WindowsKillOnCloseJob
from bot.code_integrity import CodeIntegrityError, verify_code_integrity


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "logs" / "supervisor.log"
STOP = False


def configure_logging() -> logging.Logger:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger("uzwater-supervisor")
    logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(
        LOG_PATH,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(message)s")
    )
    logger.handlers.clear()
    logger.addHandler(handler)
    return logger


def install_handlers() -> None:
    def stop(_signum: int, _frame: object) -> None:
        global STOP
        STOP = True

    signal.signal(signal.SIGINT, stop)
    signal.signal(signal.SIGTERM, stop)
    if os.name == "nt" and hasattr(signal, "SIGBREAK"):
        signal.signal(signal.SIGBREAK, stop)


def pump_stderr(process: subprocess.Popen[str], logger: logging.Logger) -> None:
    if process.stderr is None:
        return
    for line in process.stderr:
        logger.error("BOT %s", line.rstrip())


def notify_admins(logger: logging.Logger, text: str) -> None:
    try:
        import telebot

        from bot.config import load_config

        config = load_config()
        client = telebot.TeleBot(config.bot_token)
        for admin_id in config.admin_ids:
            try:
                client.send_message(admin_id, text)
            except Exception as error:
                logger.error(
                    "Admin %s ga supervisor xabari yuborilmadi: %s",
                    admin_id,
                    error,
                )
    except Exception as error:
        logger.error("Supervisor Telegram xabari tayyorlanmadi: %s", error)


def run() -> int:
    logger = configure_logging()
    install_handlers()
    try:
        verify_code_integrity(ROOT)
    except CodeIntegrityError as error:
        logger.critical("SECURITY: %s", error)
        notify_admins(
            logger,
            "🚨 UZWATERMU ishga tushirilmadi: kod yaxlitligi tekshiruvi "
            "muvaffaqiyatsiz. Serverdagi fayllarni tekshiring.",
        )
        return 4
    delay = 5
    with WindowsKillOnCloseJob() as job:
        while not STOP:
            logger.info("Bot process ishga tushirilmoqda")
            started = time.monotonic()
            process = subprocess.Popen(
                [sys.executable, "-m", "bot.main"],
                cwd=ROOT,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=(
                    subprocess.CREATE_NO_WINDOW
                    if os.name == "nt"
                    else 0
                ),
            )
            if os.name == "nt":
                job.assign(process._handle)
            stderr_thread = threading.Thread(
                target=pump_stderr,
                args=(process, logger),
                name="bot-stderr",
                daemon=True,
            )
            stderr_thread.start()
            recovery_notified = False
            while process.poll() is None and not STOP:
                if (
                    not recovery_notified
                    and time.monotonic() - started >= 15
                ):
                    notify_admins(
                        logger,
                        "✅ UZWATERMU bot ishga tushdi va barqaror ishlamoqda.",
                    )
                    recovery_notified = True
                time.sleep(1)
            if STOP and process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            stderr_thread.join(timeout=5)
            return_code = int(process.returncode or 0)
            uptime = time.monotonic() - started
            logger.warning(
                "Bot process tugadi: code=%s uptime=%.1fs",
                return_code,
                uptime,
            )
            if STOP:
                break
            if return_code == 3:
                logger.info(
                    "Boshqa bot nusxasi ishlayapti; supervisor to'xtadi"
                )
                return 3
            delay = 5 if uptime >= 300 else min(delay * 2, 300)
            notify_admins(
                logger,
                "🚨 UZWATERMU bot processi kutilmaganda to'xtadi.\n\n"
                f"Chiqish kodi: {return_code}\n"
                f"{delay} soniyadan keyin avtomatik qayta ishga tushiriladi.",
            )
            logger.info("Qayta ishga tushirishgacha %s soniya", delay)
            for _ in range(delay):
                if STOP:
                    break
                time.sleep(1)
    logger.info("Supervisor to'g'ri yopildi")
    return 0


def status() -> int:
    health_path = ROOT / "logs" / "health.json"
    if not health_path.exists():
        print("Bot: health.json topilmadi — supervisor hali ishga tushmagan.")
        return 1
    import json, os
    data = json.loads(health_path.read_text(encoding="utf-8"))
    pid = int(data.get("pid") or 0)
    state = data.get("state", "?")
    heartbeat = data.get("heartbeat_at", "?")
    started = data.get("started_at", "?")
    alive = pid and (os.name != "nt" or __import__("ctypes").windll.kernel32.OpenProcess(0x100000, False, pid) != 0)
    symbol = "✅" if alive else "❌"
    print(f"{symbol} state={state}  pid={pid}  started={started}  heartbeat={heartbeat}")
    return 0 if alive else 1


if __name__ == "__main__":
    import sys as _sys
    if len(_sys.argv) > 1 and _sys.argv[1] == "status":
        raise SystemExit(status())
    raise SystemExit(run())
