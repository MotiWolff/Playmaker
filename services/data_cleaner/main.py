# Playmaker/services/data_cleaner/main.py
from dotenv import load_dotenv
load_dotenv()

import os
import uvicorn
from pathlib import Path
import sys

base_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_path))

from Playmaker.shared.logging.logger import Logger

log = Logger.get_logger(name="playmaker.data_cleaner.main")

if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 8000))
    reload = os.getenv("RELOAD", "true").lower() == "true"

    try:
        # log before starting (since uvicorn.run() blocks)
        log.info("server.start", extra={"host": host, "port": port, "reload": reload})

        uvicorn.run("server:app", host=host, port=port, reload=reload)

        # will log after server exits cleanly
        log.info("server.stop")
    except Exception:
        # captures stack trace automatically
        log.exception("server.error")
