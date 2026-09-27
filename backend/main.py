import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

import sqlite3 as _sqlite3
from config import get_settings
from database import test_connection
from routes.auth       import router as auth_router
from routes.register   import router as register_router
from routes.projects   import router as projects_router
from routes.supervisor import router as supervisor_router
from routes.admin      import router as admin_router
from routes.alerts     import router as alerts_router
from routes.messages   import router as messages_router

settings = get_settings()
limiter  = Limiter(key_func=get_remote_address)

app = FastAPI(
    title       = "KWASU SPSEMS API",
    description = "Smart Project Supervision & Evaluation Management System",
    version     = "2.0.0",
    docs_url    = "/docs",
    redoc_url   = "/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

allowed_origins = [o.strip() for o in settings.frontend_url.split(",") if o.strip()]
for dev_url in ["http://localhost:3000", "http://localhost:3001", "http://localhost:3002", "http://127.0.0.1:3000"]:
    if dev_url not in allowed_origins:
        allowed_origins.append(dev_url)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*(\.vercel\.app|\.onrender\.com)",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs(settings.upload_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/api/uploads", StaticFiles(directory=settings.upload_dir), name="api_uploads")

def _migrate_db():
    if os.getenv("DATABASE_URL"):
        return
    try:
        import os as _os
        _base = _os.path.dirname(_os.path.abspath(__file__))
        _db   = settings.db_path if _os.path.isabs(settings.db_path) else _os.path.join(_base, settings.db_path)
        conn  = _sqlite3.connect(_db)
        try:
            conn.execute("ALTER TABLE users ADD COLUMN avatar_url TEXT")
        except Exception:
            pass
        try:
            conn.execute("ALTER TABLE submissions ADD COLUMN student_notes TEXT")
        except Exception:
            pass
        conn.commit()
        conn.close()
    except Exception:
        pass


API = "/api"
routers = [
    auth_router,
    register_router,
    projects_router,
    supervisor_router,
    admin_router,
    alerts_router,
    messages_router,
]
for r in routers:
    app.include_router(r, prefix=API)
    app.include_router(r)


@app.get("/", tags=["System"])
def root():
    return {"status": "ok", "service": "KWASU SPSEMS API", "version": "2.0.0"}


@app.get("/health", tags=["System"])
@app.get("/api/health", tags=["System"])
def health():
    return {"status": "ok", "service": "KWASU SPSEMS API", "version": "2.0.0"}


@app.on_event("startup")
def startup():
    print("\n╔══════════════════════════════════════════════╗")
    print("║   KWASU SPSEMS — FastAPI Backend v2.0       ║")
    print(f"║   Docs  : http://localhost:{settings.app_port}/docs      ║")
    print(f"║   ML svc: {settings.ml_service_url}       ║")
    print("╚══════════════════════════════════════════════╝\n")
    test_connection()
    _migrate_db()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"success": False, "message": "Internal server error.", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", settings.app_port))
    uvicorn.run("main:app", host=settings.app_host, port=port, reload=settings.debug)
