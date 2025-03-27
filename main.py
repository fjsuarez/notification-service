from fastapi import FastAPI
from config import settings
from firebase_client import lifespan
from routes import notification_routes

app = FastAPI(
    root_path="/notifications",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan)

app.include_router(notification_routes.router, tags=["Notifications"])

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)