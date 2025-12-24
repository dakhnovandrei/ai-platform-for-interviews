import logging
from fastapi import FastAPI
from src.database import engine, SessionLocal
from authx import AuthX, AuthXConfig
from src.models import Base, Users, Messages, InterviewSessions
from src.routers.websocet import chat_router
from fastapi.middleware.cors import CORSMiddleware
from src.routers.interview import interview_router
from src.routers.users import router

# Настраиваем AuthX
config = AuthXConfig()
config.JWT_SECRET_KEY = "SECRET_KEY"
config.JWT_ACCESS_COOKIE_NAME = 'my_access_token'
config.JWT_TOKEN_LOCATION = ["cookies"]
security = AuthX(config=config)

Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173",],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(router, prefix='/api/v1', tags=["Users"])
app.include_router(chat_router, tags=["Chat"])
app.include_router(interview_router, prefix='/api/v3', tags=["Interview"])

logger = logging.getLogger("uvicorn")  # использовать логгер Uvicorn
logger.setLevel(logging.INFO)


@app.on_event("startup")
def on_startup():
    logger.info("Initializing database...")
    logger.info("Tables created (if not exist).")
    db = SessionLocal()
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database connection successful.")
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
    finally:
        db.close()
