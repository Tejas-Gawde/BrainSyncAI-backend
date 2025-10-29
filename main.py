from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from db.mongodb import connect_db, close_db
from api import auth, users
from api import playgrounds, subjects, conversations

app = FastAPI()

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,  
    allow_methods=["*"],
    allow_headers=["*"],
)

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