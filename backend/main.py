import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.routers import auth, users, billing, payment, repair
from app.schemas.common import ApiResponse

app = FastAPI(title="生活缴费系统", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content=ApiResponse(code=422, message="参数校验失败", data=exc.errors()).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ApiResponse(code=exc.status_code, message=exc.detail, data=None).model_dump(),
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=ApiResponse(code=500, message="服务器内部错误", data=None).model_dump(),
    )


@app.get("/health")
def health_check():
    return {"status": "ok", "service": "life-payment"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(billing.router)
app.include_router(payment.router)
app.include_router(repair.router)
app.include_router(repair.debug_router)
