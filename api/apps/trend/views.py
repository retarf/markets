from typing import Annotated
#from sqlalchemy.sql.annotation import Annotated
from fastapi import FastAPI, Depends

from .models import Trend
from .database import engine, Session

app = FastAPI()

# models.Base.metadata.create_all(bind=engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]

@app.get("/")
def read_all(db: db_dependency):
    return db.query(Trend).all()