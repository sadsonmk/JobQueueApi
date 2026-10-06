import sqlalchemy
from fastapi import FastAPI
from app.routers import health, auth

app = FastAPI(title="JobQueue API", version="0.1.0")
app.include_router(health.router)
app.include_router(auth.router)

@app.get('/')
def home():
    return {"job" : "queueing"}
    
