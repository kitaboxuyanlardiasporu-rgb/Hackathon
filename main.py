import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from . import routes_admin, routes_auth, routes_jury
from .setup_db import init_db

logging.basicConfig(level=logging.INFO)
STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Qiymətləndirmə portalı", lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

CSP = (
    "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; "
    "font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
)


@app.middleware("http")
async def security_middleware(request: Request, call_next):
    # CSRF qorunması: dəyişiklik edən API sorğuları xüsusi başlıq tələb edir
    # (başqa saytlar bu başlığı brauzerdən göndərə bilməz).
    if request.url.path.startswith("/api/") and request.method not in ("GET", "HEAD", "OPTIONS"):
        if request.headers.get("x-requested-with") != "qiymetlendirme-portali":
            return JSONResponse({"detail": "Sorğu rədd edildi."}, status_code=403)
    response = await call_next(request)
    response.headers["Content-Security-Policy"] = CSP
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.exception_handler(RequestValidationError)
async def validation_handler(request: Request, exc: RequestValidationError):
    msg = "Daxil edilən məlumat düzgün deyil."
    for err in exc.errors():
        loc = [str(x) for x in err.get("loc", [])]
        if "value" in loc or "custom_max" in loc:
            msg = "Bal tam ədəd olmalıdır." if "value" in loc else "Maksimum bal 2 ilə 100 arasında tam ədəd olmalıdır."
            break
    return JSONResponse({"detail": msg}, status_code=422)


@app.exception_handler(StarletteHTTPException)
async def http_handler(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 404 and not request.url.path.startswith("/api/"):
        return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})
    detail = exc.detail if isinstance(exc.detail, str) else "Xəta baş verdi."
    if exc.status_code == 404 and detail == "Not Found":
        detail = "Tapılmadı."
    if exc.status_code == 405:
        detail = "İcazə verilməyən əməliyyat."
    return JSONResponse({"detail": detail}, status_code=exc.status_code)


app.include_router(routes_auth.router)
app.include_router(routes_admin.router)
app.include_router(routes_jury.router)


@app.get("/api/health")
def health():
    return {"ok": True}


app.mount("/static", StaticFiles(directory=STATIC), name="static")


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html", headers={"Cache-Control": "no-cache"})
