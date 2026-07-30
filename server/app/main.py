# app/main.py
import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.core.config import settings
from app.core.celery_app import check_celery_workers
from app.core.database import SessionLocal, check_db_connection, init_db
from app.core.fcm import init_fcm
import app.models  # noqa: F401 — registers every model on Base.metadata before create_all
from app.routes import api_router
from app.services.social import achievement_service
from app.services.shop import shop_service

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    await check_db_connection()
    await asyncio.to_thread(check_celery_workers)
    # try:
    #     init_fcm()
    # except Exception:
    #     pass  # Firebase not configured in this environment — avatar/push features will error until it is
    async with SessionLocal() as db:
        await achievement_service.ensure_seeded(db)
        await shop_service.ensure_seeded(db)
    yield


app = FastAPI(title=settings.APP_NAME, version="0.1.0", lifespan=lifespan)

# _cors_wildcard = settings.BACKEND_CORS_ORIGINS == ["*"]
# if _cors_wildcard:
#     logger.warning(
#         "BACKEND_CORS_ORIGINS is '*' — disabling allow_credentials. "
#         "Set explicit origins in .env to allow credentialed cross-origin requests."
#     )

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    # Default FastAPI behavior, but never let a validation error's raw payload
    # (which can echo back attacker input) leak more than field name + message.
    errors = [{"field": ".".join(str(p) for p in e["loc"]), "message": e["msg"]} for e in exc.errors()]
    return JSONResponse(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, content={"detail": errors})


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    # Typically a unique-constraint race (e.g. two concurrent signups with the same
    # email/username both passing the pre-check before either commits).
    logger.warning("Integrity error on %s: %s", request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "This request conflicts with existing data — please retry"},
    )


@app.exception_handler(SQLAlchemyError)
async def db_error_handler(request: Request, exc: SQLAlchemyError):
    logger.error("Database error on %s: %s", request.url.path, exc, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={"detail": "A database error occurred, please try again"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s: %s", request.url.path, exc, exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )


@app.get("/health")
async def health():
    return {"status": "ok", "app": settings.APP_NAME, "Version": "0.1.0"}
