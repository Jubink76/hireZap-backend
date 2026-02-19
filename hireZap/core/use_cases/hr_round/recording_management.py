from typing import Dict, BinaryIO
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.services.hr_round_service import VideoProcessingService
from infrastructure.services.notification_service import NotificationService
from hr_round.models import MeetingSession
import logging
logger = logging.getLogger(__name__)

# class RecordingManagementUseCase:
    
#     def __init__(self):
#         self.upload_use_case = UploadRecordingUseCase()
#         self.delete_use_case = DeleteRecordingUseCase()
    
#     def upload_recording(self, *args, **kwargs) -> Dict:
#         return self.upload_use_case.execute(*args, **kwargs)
    
#     def delete_recording(self, *args, **kwargs) -> Dict:
#         return self.delete_use_case.execute(*args, **kwargs)
    
# class UploadRecordingUseCase:
    
#     def __init__(self):
#         self.repo = HRRoundRepositoryPort()
#         self.video_service = VideoProcessingService()
#         self.notification_service = NotificationService()
    
#     def execute(
#         self,
#         interview_id: int,
#         video_file: BinaryIO,
#         filename: str,
#         duration_seconds: int = None,
#         resolution: str = None) -> Dict:
#         try:
#             interview = self.repo.get_interview_by_id(interview_id)
            
#             if not interview:
#                 return {'success': False, 'error': 'Interview not found'}
            
#             # Upload to R2
#             logger.info(f" Uploading recording for interview {interview_id}...")
#             upload_result = self.video_service.upload_recording(
#                 video_file=video_file,
#                 interview_id=interview_id,
#                 filename=filename
#             )
            
#             if not upload_result['success']:
#                 return {
#                     'success': False,
#                     'error': upload_result.get('error', 'Upload failed')
#                 }
            
#             # Save to database
#             recording = self.repo.create_recording(
#                 interview_id=interview_id,
#                 video_url=upload_result['video_url'],
#                 video_key=upload_result['video_key'],
#                 duration_seconds=duration_seconds,
#                 file_size_bytes=upload_result.get('file_size'),
#                 resolution=resolution
#             )
            
#             # Send notification to recruiter
#             self.notification_service.send_websocket_notification(
#                 user_id=interview.conducted_by_id,
#                 notification_type='recording_uploaded',
#                 data={
#                     'interview_id': interview_id,
#                     'candidate_name': interview.candidate_name,
#                     'recording_id': recording.id,
#                     'message': 'Interview recording uploaded successfully'
#                 }
#             )
            
#             logger.info(f" Recording uploaded: {upload_result['video_url']}")
            
#             # Generate thumbnail (async)
#             # from hr_interview.tasks import generate_recording_thumbnail_task
#             # generate_recording_thumbnail_task.delay(interview_id)
            
#             return {
#                 'success': True,
#                 'recording': recording
#             }
            
#         except Exception as e:
#             logger.error(f" Upload recording error: {str(e)}")
#             return {
#                 'success': False,
#                 'error': str(e)
#             }


class DeleteRecordingUseCase:
    
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        video_service: VideoProcessingService):
        
        self.repo = repository
        self.video_service = video_service
    
    def execute(self, interview_id: int, deleted_by_id: int) -> Dict:
        try:
            recording = self.repo.get_recording_by_interview(interview_id)
            
            if not recording:
                return {'success': False, 'error': 'Recording not found'}
            
            # Delete from R2
            self.video_service.delete_recording(
                video_key=recording.video_key,
                thumbnail_key=recording.thumbnail_key
            )
            
            # Delete from database
            recording.delete()
            
            logger.info(f"Recording deleted for interview {interview_id}")
            
            return {'success': True}
            
        except Exception as e:
            logger.error(f"Delete recording error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }

class ProcessZegoCloudWebhookUseCase:
    """Handle ZegoCloud webhooks"""
    
    def __init__(
        self,
        repository: HRRoundRepositoryPort,
        notification_service: NotificationService):
        
        self.repo = repository
        self.notification_service = notification_service
    
    def execute(self, webhook_data: dict) -> Dict:
        """
        Process ZegoCloud webhook
        
        Events:
        - recording.completed
        - message.sent
        - room.user_joined
        - room.user_left
        """
        try:
            event_type = webhook_data.get('event_type')
            
            if event_type == 'recording.completed':
                return self._handle_recording_completed(webhook_data)
            
            elif event_type == 'message.sent':
                return self._handle_message_sent(webhook_data)
            
            elif event_type == 'room.user_joined':
                return self._handle_user_joined(webhook_data)
            
            elif event_type == 'room.user_left':
                return self._handle_user_left(webhook_data)
            
            return {'success': True, 'message': 'Event ignored'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _handle_recording_completed(self, data: dict) -> Dict:
        """Handle recording completion webhook"""
        room_id = data.get('room_id')
        recording_url = data.get('recording_url')
        recording_id = data.get('recording_id')
        
        # Find session
        session = MeetingSession.objects.get(room_id=room_id)
        
        # Save recording URL
        self.repo.save_zegocloud_recording(
            session_id=session.session_id,
            recording_url=recording_url,
            recording_id=recording_id
        )
        
        # Create recording record
        from hr_round.models import InterviewRecording
        InterviewRecording.objects.create(
            interview_id=session.interview_id,
            video_url=recording_url,
            video_key=recording_id,
            processing_status='completed'
        )
        
        # Notify recruiter
        self.notification_service.send_websocket_notification(
            user_id=session.interview.conducted_by_id,
            notification_type='recording_uploaded',
            data={
                'interview_id': session.interview_id,
                'recording_url': recording_url
            }
        )
        
        return {'success': True}
    
    def _handle_message_sent(self, data: dict) -> Dict:
        """Handle chat message webhook"""
        room_id = data.get('room_id')
        
        # Find session
        session = MeetingSession.objects.get(room_id=room_id)
        
        # Save message
        self.repo.save_zegocloud_chat_message(
            interview_id=session.interview_id,
            message_data=data
        )
        
        return {'success': True}
    
    def _handle_user_joined(self, data: dict) -> Dict:
        """Handle user joined webhook"""
        # Update connection status if needed
        return {'success': True}
    
    def _handle_user_left(self, data: dict) -> Dict:
        """Handle user left webhook"""
        # Update connection status if needed
        return {'success': True}