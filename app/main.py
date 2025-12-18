from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.routes import auth, songs, playlists, likes, albums
from app.config import get_settings

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Music Streaming API",
    description="A complete music streaming backend with authentication, playlists, and search",
    version="1.0.0"
)

settings = get_settings()

# Add CORS middleware
# Get allowed origins from settings
allowed_origins = settings.ALLOWED_ORIGINS.split(",") if settings.ALLOWED_ORIGINS != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix=settings.API_V1_STR)
app.include_router(songs.router, prefix=settings.API_V1_STR)
app.include_router(playlists.router, prefix=settings.API_V1_STR)
app.include_router(likes.router, prefix=settings.API_V1_STR)
app.include_router(albums.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {
        "message": "Welcome to Music Streaming API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
def health_check():
    return {"status": "healthy"}
