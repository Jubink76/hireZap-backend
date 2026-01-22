from typing import Dict, BinaryIO
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
from infrastructure.services.hr_round_service import VideoProcessingService
from infrastructure.services.notification_service import NotificationService


class RecordingManagementUseCase:
    """Main use case for recording management"""
    
    def __init__(self):
        self.upload_use_case = UploadRecordingUseCase()
        self.delete_use_case = DeleteRecordingUseCase()
    
    def upload_recording(self, *args, **kwargs) -> Dict:
        """Upload recording - delegates to UploadRecordingUseCase"""
        return self.upload_use_case.execute(*args, **kwargs)
    
    def delete_recording(self, *args, **kwargs) -> Dict:
        """Delete recording - delegates to DeleteRecordingUseCase"""
        return self.delete_use_case.execute(*args, **kwargs)
    
class UploadRecordingUseCase:
    """Use case for uploading interview recording"""
    
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.video_service = VideoProcessingService()
        self.notification_service = NotificationService()
    
    def execute(
        self,
        interview_id: int,
        video_file: BinaryIO,
        filename: str,
        duration_seconds: int = None,
        resolution: str = None
    ) -> Dict:
        """
        Upload interview recording to R2
        
        Returns:
            {
                'success': bool,
                'recording': InterviewRecording,
                'error': str (if failed)
            }
        """
        try:
            interview = self.repo.get_interview_by_id(interview_id)
            
            if not interview:
                return {'success': False, 'error': 'Interview not found'}
            
            # Upload to R2
            print(f"📤 Uploading recording for interview {interview_id}...")
            upload_result = self.video_service.upload_recording(
                video_file=video_file,
                interview_id=interview_id,
                filename=filename
            )
            
            if not upload_result['success']:
                return {
                    'success': False,
                    'error': upload_result.get('error', 'Upload failed')
                }
            
            # Save to database
            recording = self.repo.create_recording(
                interview_id=interview_id,
                video_url=upload_result['video_url'],
                video_key=upload_result['video_key'],
                duration_seconds=duration_seconds,
                file_size_bytes=upload_result.get('file_size'),
                resolution=resolution
            )
            
            # Send notification to recruiter
            self.notification_service.send_websocket_notification(
                user_id=interview.conducted_by_id,
                notification_type='recording_uploaded',
                data={
                    'interview_id': interview_id,
                    'candidate_name': interview.candidate_name,
                    'recording_id': recording.id,
                    'message': 'Interview recording uploaded successfully'
                }
            )
            
            print(f"✅ Recording uploaded: {upload_result['video_url']}")
            
            # Generate thumbnail (async)
            # from hr_interview.tasks import generate_recording_thumbnail_task
            # generate_recording_thumbnail_task.delay(interview_id)
            
            return {
                'success': True,
                'recording': recording
            }
            
        except Exception as e:
            print(f"❌ Upload recording error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }


class DeleteRecordingUseCase:
    """Use case for deleting interview recording"""
    
    def __init__(self):
        self.repo = HRRoundRepositoryPort()
        self.video_service = VideoProcessingService()
    
    def execute(self, interview_id: int, deleted_by_id: int) -> Dict:
        """
        Delete interview recording
        
        Returns:
            {
                'success': bool,
                'error': str (if failed)
            }
        """
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
            
            print(f"✅ Recording deleted for interview {interview_id}")
            
            return {'success': True}
            
        except Exception as e:
            print(f"❌ Delete recording error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }