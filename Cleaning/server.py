from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from middlewares.request_logger import setup_middlewares
from db.postgres_conn import get_db
from services.cleaner import Cleaner


app = FastAPI()
setup_middlewares(app)

class TableRequest(BaseModel):
    table_name: str

@app.get('/')
def home():
    return {"response" : "Server is up."}

@app.post('/clean')
def clean(request: TableRequest, db: Session = Depends(get_db)):
    cleaner = Cleaner(db)
    result = cleaner.run_pipeline(request.table_name)
    return {"result" : result}


