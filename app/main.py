import sqlalchemy
from fastapi import FastAPI
from app.routers import health, auth, jobs

app = FastAPI(title="JobQueue API", version="0.1.0")
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(jobs.router)

@app.get('/')
def home():
    return {"job" : "queueing"}
    
