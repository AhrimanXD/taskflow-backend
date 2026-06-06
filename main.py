from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import *
# from app.core.database import engine, Base

# Create database tables
# Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Realtime Collaborative Task Manager",
    description="A collaborative task management API with real-time updates",
    version="0.1.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(tasks.router, prefix="/api/tasks", tags=["Tasks"])
app.include_router(workspace.router, prefix="/api/workspaces", tags=["Workspaces"])
app.include_router(invitation.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Realtime Collaborative Task Manager API", "version": "0.1.0"}


@app.get("/health")
def health_check():
    return {"status": "healthy"}
