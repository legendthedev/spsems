from pydantic_settings import BaseSettings
from pydantic import field_validator
from functools import lru_cache


class Settings(BaseSettings):
    # SQLite — no server or admin required
    db_path: str = "spsems.db"

    # JWT
    jwt_secret:       str = "kwasu_spsems_jwt_secret_2026"
    jwt_algorithm:    str = "HS256"
    jwt_expire_hours: int = 24

    # Server
    app_host:  str  = "0.0.0.0"
    app_port:  int  = 8000
    debug:     bool = True

    # ML microservice (separate process on port 8001)
    ml_service_url: str = "http://localhost:8001"

    @field_validator("ml_service_url", mode="after")
    @classmethod
    def normalize_ml_url(cls, v: str) -> str:
        if not v:
            return "http://localhost:8001"
        v = v.strip().rstrip("/")
        if not (v.startswith("http://") or v.startswith("https://")):
            if "localhost" in v or "127.0.0.1" in v:
                return f"http://{v}"
            if "." not in v:
                return f"https://{v}.onrender.com"
            return f"https://{v}"
        return v

    # File uploads
    upload_dir:       str = "./uploads"
    max_file_size_mb: int = 10

    # Admin self-registration code
    admin_reg_code: str = "KWASU-HOD-2026"

    # CORS
    frontend_url: str = "http://localhost:3000"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


@lru_cache()
def get_settings() -> Settings:
    return Settings()
