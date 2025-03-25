from fastapi import APIRouter, HTTPException, Request
from models import Notification, TokenRegistration
from services.notification_service import create_notification, get_notification, send_notification, register_token
from typing import Dict, Any

router = APIRouter()

@router.get("/health", include_in_schema=False)
async def health_check():
    return {"status": "ok"}

@router.get("/{notification_id}", response_model=Notification)
async def get_notification_endpoint(notification_id: str, request: Request):
    notifications_ref = request.app.state.notifications_ref
    if not notifications_ref:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        notification = await get_notification(notifications_ref, notification_id)
        if not notification:
            raise HTTPException(status_code=404, detail="Notification not found")
        return notification
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error fetching notification: {exc}")

@router.post("/", response_model=Notification)
async def create_notification_endpoint(notification: Notification, request: Request):
    notifications_ref = request.app.state.notifications_ref
    if not notifications_ref:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        notification_data = notification.model_dump(by_alias=True)
        result = await create_notification(notifications_ref, notification_data)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error creating notification: {exc}")

@router.post("/send", status_code=201)
async def send_notification_endpoint(request: Request):
    notifications_ref = request.app.state.notifications_ref
    tokens_ref = request.app.state.tokens_ref
    
    if not notifications_ref or not tokens_ref:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        data = await request.json()
        user_id = data.get('userId')
        title = data.get('title')
        body = data.get('body')
        
        if not all([user_id, title, body]):
            raise HTTPException(status_code=400, detail="Missing required fields")
            
        result = await send_notification(
            notifications_ref, tokens_ref, user_id, title, body, data.get('data', {})
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error sending notification: {exc}")

@router.post("/tokens")
async def register_token_endpoint(request: Request):
    tokens_ref = request.app.state.tokens_ref
    if not tokens_ref:
        raise HTTPException(status_code=500, detail="Firestore not initialized")
    
    try:
        data = await request.json()
        user_id = data.get('userId')
        token = data.get('token')
        
        if not user_id or not token:
            raise HTTPException(status_code=400, detail="Missing userId or token")
        
        result = await register_token(tokens_ref, user_id, token)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Error registering token: {exc}")