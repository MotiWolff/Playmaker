# Playmaker/services/data_cleaner/server.py
from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from middlewares.request_logger import setup_middlewares
from db.postgres_conn import get_db
from services.cleaner import Cleaner

from Playmaker.shared.logging.logger import Logger

# project-wide hierarchical logger
log = Logger.get_logger(name="playmaker.data_cleaner.server")

app = FastAPI()
setup_middlewares(app)

# lifecycle logs
@app.on_event("startup")
async def _startup():
    log.info("fastapi.startup")

@app.on_event("shutdown")
async def _shutdown():
    log.info("fastapi.shutdown")

class TableRequest(BaseModel):
    table_name: str

@app.get("/")
def home():
    log.debug("home.request")
    return {"response": "Server is up."}

@app.post("/clean")
def clean(request: TableRequest, db: Session = Depends(get_db)):
    log.info("clean.request", extra={"table": request.table_name})
    try:
        cleaner = Cleaner(db, request.table_name)
        result = cleaner.run_pipeline()
        log.info("clean.success", extra={"table": request.table_name})
        return {"result": result}
    except Exception:
        # full traceback goes to console/ES via Logger
        log.exception("clean.error", extra={"table": request.table_name})
        raise
