from fastapi import FastAPI

from api.routers import User

app = FastAPI()

from api.database import reset_database
reset_database()

app.include_router(User.router)