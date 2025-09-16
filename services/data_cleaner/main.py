"""
Entry point for running the Clean server using Uvicorn.

This script:
    - Loads environment variables from a .env file.
    - Sets the base project path to allow proper imports.
    - Configures logging using the shared Logger.
    - Starts the FastAPI server with Uvicorn on the configured host and port.
"""

from dotenv import load_dotenv
load_dotenv()
import os
import uvicorn
from pathlib import Path
import sys

base_path = Path(__file__).resolve().parent.parent.parent
sys.path.append(str(base_path))

from server import app
from shared.logging.logger import Logger


my_logger = Logger.get_logger()

if __name__ == "__main__":
    try: 
        uvicorn.run(
            "server:app",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", 8000)),
            reload=True
        )
        my_logger.info(f"Clean server is up on port:{os.getenv("PORT")}")
    except Exception as e:
        my_logger.error(f"Error running clean server.\nError:{e}")