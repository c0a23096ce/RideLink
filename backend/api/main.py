from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import User, Websocket, Matching, RouteGenerate

app = FastAPI()

from database import reset_database
reset_database()

app.include_router(User.router)
app.include_router(Matching.router)
app.include_router(RouteGenerate.router)
app.include_router(Websocket.router)

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

@app.exception_handler(RequestValidationError)
async def handler(request:Request, exc:RequestValidationError):
    print(exc)
    return JSONResponse(content={}, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

origins = [
    "http://localhost:3000",  # Next.jsのURL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,              # 許可するオリジン
    allow_credentials=True,             # Cookie認証を許可する
    allow_methods=["*"],                # 全てのHTTPメソッドを許可（GET, POSTなど）
    allow_headers=["*"],                # 全てのヘッダーを許可
)