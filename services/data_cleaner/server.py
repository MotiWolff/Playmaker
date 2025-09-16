from fastapi import FastAPI, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from middlewares.request_logger import setup_middlewares
from db.postgres_conn import get_db
from services.cleaner import Cleaner


app = FastAPI()
setup_middlewares(app)

class TableRequest(BaseModel):
    """
    Request model for cleaning a database table.

    Attributes:
        table_name (str): The name of the database table to be cleaned.
    """
    table_name: str

@app.get('/')
def home():
    """
    Health check endpoint.

    Returns:
        dict: A JSON response confirming that the server is running.
    """
    return {"response" : "Server is up."}

@app.post('/clean')
def clean(request: TableRequest, db: Session = Depends(get_db)):
    """
    Clean a specified database table by running the cleaning pipeline.

    Args:
        request (TableRequest): Request body containing the table name.
        db (Session): SQLAlchemy session provided via dependency injection.

    Returns:
        dict: The result of the cleaning pipeline.
    """
    cleaner = Cleaner(db, request.table_name)
    result = cleaner.run_pipeline()
    return {"response" : result}


