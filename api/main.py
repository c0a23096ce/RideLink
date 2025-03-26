from fastapi import FastAPI

from api.routers import User, Websocket, Matching

app = FastAPI()

from api.database import reset_database
reset_database()

app.include_router(User.router)
app.include_router(Matching.router)
app.include_router(Websocket.router)