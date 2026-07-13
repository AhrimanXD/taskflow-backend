from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.routes import *
from app.websocket import routes as ws_routes
# from app.core.database import engine, Base

# Create database tables
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Realtime Collaborative Task Manager",
    description="A collaborative task management API with real-time updates",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=settings.cors_origin_regex,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(workspace.router, prefix="/api/workspaces", tags=["Workspaces"])
app.include_router(invitation.router, prefix="/api")
app.include_router(workspace_tasks.router, prefix="/api")
app.include_router(comments.router, prefix="/api")
app.include_router(stats.router, prefix="/api/stats", tags=["Stats"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["Notifications"])
app.include_router(ws_routes.router)  # WS path already starts with /ws — no prefix


@app.get("/")
def root():
    return {"message": "Realtime Collaborative Task Manager API", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
