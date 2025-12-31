from abc import ABC, abstractmethod
from typing import Dict

class NotificationServicePort(ABC):
    
    @abstractmethod
    def send_websocket_notification(self, user_id: int, notification_type: str, data: Dict):
        """Send WebSocket notification to user"""
        pass
    
    @abstractmethod
    def send_screening_result_email(self, application_id: int, decision: str, score: int):
        """Send screening result email"""
        pass
    
    @abstractmethod
    def send_stage_progress_email(self, application_id: int, current_stage: str, next_stage: str):
        """Send stage progression email"""
        pass