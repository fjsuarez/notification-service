from firebase_admin import messaging
from models import Notification
from typing import Dict, Any, List
from datetime import datetime
from uuid import uuid4
import logging

async def get_notification(notifications_ref, notification_id: str):
    """Get a notification by ID"""
    try:
        doc = notifications_ref.document(notification_id).get()
        if not doc.exists:
            return None
        return doc.to_dict()
    except Exception as exc:
        logging.error(f"Error fetching notification: {exc}")
        raise

async def create_notification(notifications_ref, notification_data: Dict[str, Any]):
    """Create a notification record"""
    try:
        # Generate ID if not provided
        if 'notificationId' not in notification_data:
            notification_data['notificationId'] = f"notification_{uuid4().hex}"
        
        # Set timestamps if not provided
        if 'createdAt' not in notification_data:
            notification_data['createdAt'] = datetime.now()
            
        notification_ref = notifications_ref.document(notification_data['notificationId'])
        notification_ref.set(notification_data)
        
        return notification_data
    except Exception as exc:
        logging.error(f"Error creating notification: {exc}")
        raise

async def send_notification(notifications_ref, tokens_ref, user_id: str, title: str, body: str, data: Dict[str, Any] = None):
    """Send a push notification to a user via FCM"""
    try:
        logging.info(f"Sending notification to user {user_id} with title: {title}")
        
        # Get user tokens
        tokens_doc = tokens_ref.document(user_id).get()
        if not tokens_doc.exists:
            return {"status": "error", "message": "No tokens found for this user"}
            
        tokens = tokens_doc.to_dict().get("tokens", [])
        if not tokens:
            return {"status": "error", "message": "User has no registered tokens"}
        
        # Create notification record first
        notification_ref = notifications_ref.document()
        notification_data = {
            "notificationId": notification_ref.id,
            "userId": user_id,
            "title": title,
            "body": body,
            "data": data or {},
            "isRead": False,
            "createdAt": datetime.now(),
        }
        notification_ref.set(notification_data)
        
        # Convert any non-string values in data to strings
        # FCM requires all data values to be strings
        string_data = {}
        if data:
            for key, value in data.items():
                string_data[key] = str(value) if value is not None else ""
        
        # Send messages individually with proper format for both foreground and background
        success_count = 0
        failure_count = 0
        
        for token in tokens:
            try:
                # Create message with format that works for both foreground and background
                message = messaging.Message(
                    token=token,
                    notification=messaging.Notification(
                        title=title,
                        body=body,
                    ),
                    data=string_data,
                    # Add webpush configuration
                    webpush=messaging.WebpushConfig(
                        headers={
                            "TTL": "86400",
                            "Urgency": "high",
                            "priority": "high"
                        },
                        # This ensures the notification appears properly
                        notification=messaging.WebpushNotification(
                            title=title,
                            body=body,
                            icon="/assets/logo.png"
                        )
                    ),
                    # Add Android configuration
                    android=messaging.AndroidConfig(
                        priority="high"
                    )
                )
                
                # Send message and log response
                response = messaging.send(message)
                logging.info(f"Notification sent successfully: {response}")
                success_count += 1
            except Exception as e:
                logging.error(f"Failed to send to token {token[:20]}...: {e}", exc_info=True)
                failure_count += 1
        
        return {
            "status": "success", 
            "sent": success_count,
            "failed": failure_count,
            "notificationId": notification_ref.id
        }
    except Exception as exc:
        logging.error(f"Error sending notification: {exc}", exc_info=True)
        raise

async def register_token(tokens_ref, user_id: str, token: str):
    """Register a FCM token for a user"""
    try:
        tokens_doc = tokens_ref.document(user_id).get()
        
        if tokens_doc.exists:
            tokens = tokens_doc.to_dict().get("tokens", [])
            if token not in tokens:
                tokens.append(token)
                tokens_ref.document(user_id).update({"tokens": tokens})
        else:
            tokens_ref.document(user_id).set({"tokens": [token]})
            
        return {"status": "success", "message": "Token registered successfully"}
    except Exception as exc:
        logging.error(f"Error registering token: {exc}")
        raise