import os

class Settings:
    PROJECT_NAME: str = "NeoStats Document Intelligence Platform"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: list[str] = [
        origin.strip() for origin in os.getenv("NEOSTATS_CORS_ORIGINS", "*").split(",")
        if origin.strip()
    ]
    
    # Validation constraints per assessment PDF (Section 3 & 4.1)
    MAX_FILE_SIZE_MB: int = 10
    MAX_PAGE_COUNT: int = 3
    ALLOWED_EXTENSIONS: set = {"pdf", "jpg", "jpeg", "png"}
    ALLOWED_MIME_TYPES: set = {
        "application/pdf",
        "image/jpeg",
        "image/png",
        "image/jpg"
    }

    # DB Config
    DB_PATH: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "neostats.db")

settings = Settings()
