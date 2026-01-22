from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from django.utils import timezone

class HRRoundRepositoryPort(ABC):

    @abstractmethod
    def get_settings_by_id(self, job_id:int):
        """Get HR round Settings  for a job"""
        return NotImplementedError
    
    @abstractmethod
    def create_default_settings(self, job_id:int):
        """Create default settings for a job"""
        return NotImplementedError
    
    @abstractmethod
    def update_settings(self, job_id:int, settings_data:Dict):
        """Update or create settings"""
        return NotImplementedError
    
    @abstractmethod
    def create_interview(self, application_id:int, job_id:int, stage_id:int=None):
        """Create new hr round record"""
        return NotImplementedError
    
    @abstractmethod
    def get_interview_by_id(self, interview_id:int):
        """Get interview by ID"""
        return NotImplementedError
    
    @abstractmethod
    def get_interview_by_application(self, application_id:int):
        """Get interview by application"""
        return NotImplementedError
    
    @abstractmethod
    def list_interviews_by_job(self, job_id:int, status:str=None) ->List:
        """List interview for a job"""
        return NotImplementedError
    
    @abstractmethod
    def list_interviews_by_recruiter(self, recruiter_id:int, status:str=None)->List:
        """List interviews by recruiter"""
        return NotImplementedError
    
    @abstractmethod
    def schedule_interview(self,
                           application_id:int,
                           scheduled_at:timezone.datetime,
                           duration_minutes:int,
                           timezone_str:str,
                           conducted_by_id:int,
                           scheduling_notes:str=None):
        """Schedule interview"""
        return NotImplementedError
    
    @abstractmethod
    def bulk_schedule_interview(self,
                                application_ids:List[int],
                                scheduled_at:timezone.datetime,
                                duration_minutes:int,
                                timezone_str:str,
                                conducted_by_id:int,
                                scheduling_notes:str=None)->List:
        """Schedule multiple interviews at once"""
        return NotImplementedError
    
    @abstractmethod
    def update_interview_status(self, interview_id:int, status:str, **kwargs):
        """Update interview status"""
        return NotImplementedError
    
    @abstractmethod
    def cancel_interview(self, interview_id:int, reason:str):
        """Cancel interview"""
        return NotImplementedError
    
    @abstractmethod
    def mark_notification_sent(self, interview_id:int):
        """Mark notification sent"""
        return NotImplementedError
    
    @abstractmethod
    def mark_email_sent(self, interview_id:int):
        """Mark email sent"""
        return NotImplementedError
    
    @abstractmethod
    def mark_reminder_sent(self, interview_id:int):
        """Mark reminder sent"""
        return NotImplementedError
    
    @abstractmethod
    def get_upcoming_interviews_for_reminder(self, hours_before:int=24):
        """Get interviews that need reminders"""
        return NotImplementedError
    
    @abstractmethod
    def create_meeting_session(self, interview_id:int, recruiter_id:int, candidate_id:str):
        """Create meeting session"""
        return NotImplementedError
    
    @abstractmethod
    def get_meeting_session(self, session_id:int):
        """Get meeting session by session id"""
        return NotImplementedError
    
    @abstractmethod
    def get_meeting_session_by_interview(self, interview_id:int):
        """Get meeting session by interview"""
        return NotImplementedError
    
    @abstractmethod
    def update_participant_connection(self, session_id:str, participant_type:str, connected:bool):
        """Update participant connection status"""
        return NotImplementedError
    
    @abstractmethod
    def start_recording(self, session_id:str):
        """Start recording"""
        return NotImplementedError
    
    @abstractmethod
    def stop_recording(self, session_id:str):
        """"Stop recording"""
        return NotImplementedError
    
    @abstractmethod
    def end_meeting_session(self, session_id:str):
        """End meeting session"""
        return NotImplementedError
    
    @abstractmethod
    def create_recording(self,
                         interview_id:int,
                         video_url:str,
                         video_key:str,
                         duration_seconds:int=None,
                         file_size_bytes:int=None,
                         resolution:str=None):
        """Create recording record"""
        return NotImplementedError
    
    @abstractmethod
    def update_recording_thumbnail(self,
                                   interview_id:int,
                                   thumbnail_url:str,
                                   thumbnail_key:str,
                                   ):
        """Update recording thumbanail"""
        return NotImplementedError
    
    @abstractmethod
    def get_recording_by_interview(self, interview_id:int):
        """Get recording by interiview"""
        return NotImplementedError
    
    @abstractmethod
    def create_or_update_notes(self,interview_id:int, recoreded_by_id:int,notes_data:Dict):
        """Create or update interview notes"""
        return NotImplementedError
    
    @abstractmethod
    def get_notes_by_interview(self, interview_id:int):
        """Get notes by interview"""
        return NotImplementedError
    
    @abstractmethod
    def finilize_notes(self, interview_id:int):
        """Finalize notes"""
        return NotImplementedError
    
    @abstractmethod
    def save_chat_message(self, interview_id:int, sender_id:str, sender_type:str,message:str, is_system_message:bool=False):
        """Save chat message to database"""
        return NotImplementedError
    
    @abstractmethod
    def get_chat_messages(self, interview_id:int, limit:int =100):
        """Get chat messages for interview"""
        return NotImplementedError
    
    @abstractmethod
    def delete_chat_messages(self, interview_id:int):
        """Delete all chat messages for interview"""
        return NotImplementedError
    @abstractmethod
    def create_or_update_result(self,
                                interview_id:int,
                                final_score:int,
                                decision:str,
                                decided_by_id:int,
                                decision_reason:str=None,
                                next_steps:str=None):
        """Create or update interview result"""
        return NotImplementedError
    
    @abstractmethod
    def get_result_by_interview(self,interview_id:int):
        """Get result by interview"""
        return NotImplementedError
    

