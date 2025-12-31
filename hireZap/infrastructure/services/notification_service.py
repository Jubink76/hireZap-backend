from typing import Dict
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from core.interface.notification_service_port import NotificationServicePort

class NotificationService(NotificationServicePort):
    
    def send_websocket_notification(self, user_id: int, notification_type: str, data: Dict):
        """Send WebSocket notification to user"""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{user_id}',
                {
                    'type': notification_type,
                    **data
                }
            )
        except Exception as e:
            print(f"WebSocket notification failed: {str(e)}")
    
    def send_screening_result_email(self, application_id: int, decision: str, score: int):
        """Send screening result email (triggers Celery task)"""
        from resume_screening.tasks import send_screening_result_email_task
        send_screening_result_email_task.delay(application_id, decision, score)
        
    
    def send_stage_progress_email(self, application_id: int, current_stage: str, next_stage: str):
        """Send stage progression email (triggers Celery task)"""
        from resume_screening.tasks import send_stage_progress_email_task
        send_stage_progress_email_task.delay(application_id, current_stage, next_stage)
        