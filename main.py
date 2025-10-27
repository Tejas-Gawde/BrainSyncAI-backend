from fastapi import FastAPI
from db.mongodb import connect_db
from api import auth, users
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="FastAPI Mongo JWT Auth")

# Connect DB at startup
@app.on_event("startup")
async def startup_event():
    await connect_db()


# Simple CORS config, adjust origins in prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # change as required
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
