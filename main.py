from fastapi import FastAPI, HTTPException
from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, firestore
from models import Notification

class Settings(BaseSettings):
    PORT: int
    DATABASE_URL: str

    model_config = ConfigDict(env_file='.env')
settings = Settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- Startup ---
    try:
        cred = credentials.Certificate('credentials.json')
        firebase_app = firebase_admin.initialize_app(cred, {
            'databaseURL': settings.DATABASE_URL
        })
        db = firestore.client(app=firebase_app, database_id="notifications")
        notifications_ref = db.collection("notifications")
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")

    app.state.notifications_ref = notifications_ref
    yield

    # --- Shutdown ---
    try:
        if db:
            print("Closing Firestore client...")
            db.close()
            print("Firestore client closed.")
        if firebase_app:
            firebase_admin.delete_app(firebase_app)
            print("Firebase Admin SDK app deleted successfully.")
    except Exception as e:
        print(f"Error deleting Firebase Admin SDK app: {e}")

app = FastAPI(
    root_path="/notifications",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan)

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/", response_model=Notification)
async def create_notification(notification: Notification):
    # Convert the model into a dictionary using aliases for Firestore
    notification_data = notification.model_dump(by_alias=True)
    try:
        # Write the notification document using notificationId as the document ID
        doc_ref = app.state.notifications_ref.document(notification.notificationId)
        doc_ref.set(notification_data)
        return notification  # will be serialized using Notification model
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {exc}")

@app.get("/{notification_id}", response_model=Notification)
async def get_notification(notification_id: str):
    try:
        doc = app.state.notifications_ref.document(notification_id).get()
        if doc.exists:
            data = doc.to_dict()
            try:
                # Validate and parse the Firestore data with the Notification model
                return Notification.model_validate(data)
            except Exception as exc:
                raise HTTPException(status_code=500, detail=f"Error parsing notification: {exc}")
        else:
            raise HTTPException(status_code=404, detail="Notification not found")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error fetching notification: {exc}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)