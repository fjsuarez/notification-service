from fastapi import FastAPI
from contextlib import asynccontextmanager
import firebase_admin
from firebase_admin import credentials, firestore
from config import settings

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
        tokens_ref = db.collection("tokens")
        print("Firebase Admin SDK initialized successfully.")
    except Exception as e:
        print(f"Error initializing Firebase Admin SDK: {e}")

    app.state.notifications_ref = notifications_ref
    app.state.tokens_ref = tokens_ref
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