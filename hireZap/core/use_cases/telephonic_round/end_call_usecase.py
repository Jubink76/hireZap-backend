"""
core/use_cases/telephonic_round/end_call_usecase.py
"""
from typing import Dict, Optional, BinaryIO
from django.utils import timezone
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from core.interface.storage_repository_port import StorageRepositoryPort
from infrastructure.services.notification_service import NotificationService


class EndCallUseCase:
    """
    End telephonic interview call and save recording
    """
    
    def __init__(
        self,
        repository: TelephonicRoundRepositoryPort,
        storage: StorageRepositoryPort,
        notification_service: NotificationService
    ):
        self.repository = repository
        self.storage = storage
        self.notification_service = notification_service
    
    def execute(
        self,
        session_id: str,
        duration_seconds: int,
        recording_file: Optional[BinaryIO] = None,
        connection_quality: str = 'good'
    ) -> Dict:
        """
        End call and process recording
        
        Args:
            session_id: Call session ID
            duration_seconds: Actual call duration in seconds
            recording_file: Audio recording file (optional)
            connection_quality: Connection quality rating
        
        Returns:
            {
                'success': bool,
                'interview_id': int,
                'recording_url': str,
                'message': str
            }
        """
        
        # 1. Get call session
        call_session = self.repository.get_call_session_by_id(session_id)
        
        if not call_session:
            return {
                'success': False,
                'error': 'Call session not found'
            }
        
        interview = call_session.interview
        
        # 2. Validate call is in progress
        if interview.status != 'in_progress':
            return {
                'success': False,
                'error': f'Call is not in progress. Current status: {interview.status}'
            }
        
        # 3. Upload recording if provided
        recording_url = None
        recording_key = None
        recording_size = 0
        
        if recording_file:
            try:
                # Validate audio file
                from infrastructure.services.telephonic_service import AudioProcessorService
                validation = AudioProcessorService.validate_audio_file(recording_file)
                
                if not validation['valid']:
                    return {
                        'success': False,
                        'error': f"Invalid audio file: {validation['error']}"
                    }
                
                recording_size = recording_file.size
                
                # Upload to R2 storage
                filename = f"interview_{interview.id}_{session_id}.wav"
                upload_result = self.storage.upload_file(
                    file=recording_file,
                    folder='interview_recordings',
                    filename=filename,
                    content_type='audio/wav',
                    make_public=False  # Keep recordings private
                )
                
                if not upload_result.get('success'):
                    return {
                        'success': False,
                        'error': 'Failed to upload recording'
                    }
                
                recording_url = upload_result['url']
                recording_key = upload_result['key']
                
            except Exception as e:
                return {
                    'success': False,
                    'error': f'Recording upload failed: {str(e)}'
                }
        
        # 4. End call session
        call_session = self.repository.end_call_session(
            session_id=session_id,
            recording_url=recording_url or '',
            recording_key=recording_key or '',
            duration_seconds=duration_seconds,
            recording_size_bytes=recording_size
        )
        
        # 5. Update call session quality
        self.repository.update_call_session(
            session_id=session_id,
            connection_quality=connection_quality
        )
        
        # 6. Update interview status
        interview = self.repository.update_interview_status(
            interview_id=interview.id,
            status='completed',
            ended_at=timezone.now(),
            actual_duration_seconds=duration_seconds
        )
        
        # 7. Send notifications
        self._notify_call_ended(interview)
        
        # 8. Trigger background processing if recording exists
        if recording_url:
            self._trigger_recording_processing(session_id)
            message = 'Call ended successfully. Recording is being processed...'
        else:
            message = 'Call ended successfully. No recording available.'
        
        return {
            'success': True,
            'interview_id': interview.id,
            'session_id': session_id,
            'recording_url': recording_url,
            'duration': duration_seconds,
            'message': message
        }
    
    def _notify_call_ended(self, interview):
        """Send notifications that call has ended"""
        
        # Notify candidate
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='call_ended',
            data={
                'interview_id': interview.id,
                'job_title': interview.job.job_title,
                'duration': interview.actual_duration_seconds,
                'message': 'Interview call ended. Results will be shared soon.'
            }
        )
        
        # Notify recruiter
        if interview.conducted_by_id:
            self.notification_service.send_websocket_notification(
                user_id=interview.conducted_by_id,
                notification_type='call_ended',
                data={
                    'interview_id': interview.id,
                    'candidate_name': f"{interview.application.first_name} {interview.application.last_name}",
                    'duration': interview.actual_duration_seconds,
                    'message': 'Call ended. Processing recording...'
                }
            )
    
    def _trigger_recording_processing(self, session_id: str):
        """Trigger Celery task to process recording"""
        from telephonic_round.tasks import process_interview_recording_task
        
        # Delay to ensure all data is committed
        process_interview_recording_task.apply_async(
            args=[session_id],
            countdown=5  # Wait 5 seconds before starting
        )