import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app.database import init_db, close_pool, get_connection, release_connection
from app.models import IdentifyRequest, IdentifyResponse
from app.service import identify
from app.exceptions import (
    DatabaseConnectionError,
    ContactNotFoundError,
    InvalidRequestError,
    database_connection_error_handler,
    contact_not_found_error_handler,
    invalid_request_error_handler,
)

from dotenv import load_dotenv
load_dotenv()

# ─── Logging ────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format='{"time": "%(asctime)s", "level": "%(levelname)s", "message": "%(message)s"}'
)
logger = logging.getLogger(__name__)


# ─── Lifespan ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up — initializing database connection pool")
    init_db()
    yield
    logger.info("Shutting down — closing database connection pool")
    close_pool()


# ─── App ────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Identity Reconciliation",
    description="Bitespeed identity reconciliation service",
    version="1.0.0",
    lifespan=lifespan
)


# ─── Middleware ──────────────────────────────────────────────────────────────

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    import uuid
    request_id = str(uuid.uuid4())
    logger.info(f"Incoming request | id={request_id} method={request.method} path={request.url.path}")
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(f"Completed request | id={request_id} status={response.status_code}")
    return response


# ─── Prometheus ──────────────────────────────────────────────────────────────

Instrumentator().instrument(app).expose(app)


# ─── Exception Handlers ──────────────────────────────────────────────────────

app.add_exception_handler(DatabaseConnectionError, database_connection_error_handler)
app.add_exception_handler(ContactNotFoundError, contact_not_found_error_handler)
app.add_exception_handler(InvalidRequestError, invalid_request_error_handler)


# ─── Routes ──────────────────────────────────────────────────────────────────

GRAFANA_URL = os.getenv("GRAFANA_URL", "http://localhost:3000")

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/dashboard")
def dashboard():
    return RedirectResponse(url=GRAFANA_URL)


@app.post("/identify", response_model=IdentifyResponse)
def identify_contact(body: IdentifyRequest):
    conn = get_connection()
    try:
        return identify(body.email, body.phoneNumber, conn)
    finally:
        release_connection(conn)