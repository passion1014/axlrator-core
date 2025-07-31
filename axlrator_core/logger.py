import logging
from logging.handlers import TimedRotatingFileHandler
import os

log_dir = os.path.expanduser("~/logs")
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, "axlrator-core.log")

handler = TimedRotatingFileHandler(
    filename=log_file,
    when="midnight",
    interval=1,
    backupCount=7,
    encoding="utf-8"
)

formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
handler.setFormatter(formatter)

logger = logging.getLogger("axlrator")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False  # 루트 로거로 중복 전파 방지
