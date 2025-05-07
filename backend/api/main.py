import asyncio
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from routers import User, Matching, Matched, Websocket
from database import reset_database
# ← ★ WebSocketサービスをインポート
from services.ConnectionManager import ConnectionManager
from services.MatchingService import MatchingService

app = FastAPI()

# ← ★ WebSocketとMatchingServiceのインスタンスを作ってアプリに登録
connection_manager = ConnectionManager()
matching_service = MatchingService()
matching_service.set_connection_manager(connection_manager)

app.state.connection_manager = connection_manager
app.state.matching_service = matching_service

@app.on_event("startup")
async def startup_event():
    # アプリケーション起動時にデータベースをリセット
    await reset_database()
    import logging
    logging.getLogger("sqlalchemy.engine").disabled = True

# ルーター登録
app.include_router(User.router)
app.include_router(Matching.router)
app.include_router(Matched.router)
app.include_router(Websocket.router)


# バリデーションエラーをJSONで返す
@app.exception_handler(RequestValidationError)
async def handler(request: Request, exc: RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

# CORS設定
origins = ["http://localhost:5173"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
