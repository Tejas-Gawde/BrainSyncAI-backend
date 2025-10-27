from fastapi import FastAPI
from db.mongodb import connect_db, close_db
from api import auth, users  # existing
from api import playgrounds, subjects, conversations  # new

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await connect_db()

@app.on_event("shutdown")
async def shutdown_event():
    await close_db()

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(playgrounds.router)
app.include_router(subjects.router)
app.include_router(conversations.router)
