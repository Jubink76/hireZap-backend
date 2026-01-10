from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class TelephonicRoundRepositoryPort(ABC):

    @abstractmethod
    def get_settings_by_id(self, job_id:int):
        """Get telephonic settings for a job"""
        return NotImplementedError
    
    @abstractmethod
    def create_default_settings(self, job_id:int):
        """Create default settings for a job"""
        return NotImplementedError
    
    @abstractmethod
    def update_settings(self, job_id:int, settings_dat:Dict):
        """Update settings"""
        return NotImplementedError

    @abstractmethod
    def get_interview_by_id(self, interview_id:int):
        """Get interview by id with related data"""
        return NotImplementedError
    
    @abstractmethod
    def get_interview_by_application(self, application_id:int):
        """Get interview for an application"""
        return NotImplementedError
    
    @abstractmethod
    def get_interviews_by_job(self, job_id:int, status:Optional[str] = None):
        """ Get all interviews for a job"""
        return NotImplementedError
    
    @abstractmethod
    def get_candidates_for_telephonic_round(self, job_id:int, stage_id:Optional[int]=None):
        """Get candidates who qualifiedd from previous stage for telephonic roundd"""
        return NotImplementedError
    
    @abstractmethod
    def get_unscheduled_interviews(self, job_id:int):
        """Get interviews that haven't been scheduled yet"""
        return NotImplementedError
    
    @abstractmethod
    def get_scheduled_interviews(self, job_id:int):
        """Get scheduled interviews"""
        return NotImplementedError
    
    @abstractmethod
    def get_completed_interviews(self,job_id:int):
        """Get completed interviews"""

    @abstractmethod
    def create_interview(self, application_id:int, **kwargs):
        """Create a new interview"""
        return NotImplementedError
    
    @abstractmethod
    def update_interview_status(self, interview_id:int, status:str, **kwargs):
        """Update interview statsu"""
        return NotImplementedError
    
    @abstractmethod
    def schedule_interview(self, interview_id:int, scheduled_at, duration:int, timezone:str, notes:Optional[str]=None):
        """Schedule an interview"""
        return NotImplementedError
    
    @abstractmethod
    def bulk_create_interview(self,
                              applications:List):
        """Create interview records for multiple applications"""
        return NotImplementedError
    
    @abstractmethod
    def create_call_session(self,interview_id:int, session_id:str,caller_id:str,callee_id:str):
        """Create call session"""
        return NotImplementedError
    
    @abstractmethod
    def get_call_session_by_id(self, session_id:str):
        """Get call session by session Id"""
        return NotImplementedError
    
    @abstractmethod
    def update_call_session(self,session_id:str, **kwargs):
        """Update call session"""
        return NotImplementedError
    
    @abstractmethod
    def end_call_session(self,
                         session_id:str,
                         recording_url:str,
                         recording_key:str,
                         duration_seconds:int,
                         recording_size_bytes:int):
        """End call and save recording info"""
        return NotImplementedError
    
    @abstractmethod
    def create_transcription(self, 
                             interview_id:int,
                             full_text:str,
                             segments:List[Dict],
                             detected_language:str='en',
                             confidence:Optional[float]=None):
        """Create transcription record"""
        return NotImplementedError
    
    @abstractmethod
    def update_transcription_status(self,
                                    interview_id:int,
                                    status:str,
                                    error_message:Optional[str]=None):
        """Update transcription processing status"""
        return NotImplementedError
    
    @abstractmethod
    def save_performance_result(self,
                                interview_id:int,
                                scores:Dict,
                                decision:str,
                                analysis:Dict):
        """Save ai analysed performance results"""
        return NotImplementedError
    
    @abstractmethod
    def update_manual_score(self,
                            interview_id:int,
                            manual_score:int,
                            manual_decision:str,
                            override_reason:str,
                            override_by_id:int):
        """Update with manual score override"""
        return NotImplementedError
    
    @abstractmethod
    def get_performance_result(self, interview_id:int):
        """Get performance result"""
        return NotImplementedError
    
    @abstractmethod
    def get_job_interview_stats(self, job_id:int):
        """Get statistics for a job"""
        return NotImplementedError
    
    @abstractmethod
    def move_interviews_to_next_stage(self,
                           interview_ids:List[int],
                           feedback:str=''):
        """Move qualified candidate to next stage"""
        return NotImplementedError
    
    @abstractmethod
    def get_upcoming_interviews_for_reminder(self, hours_before:int=24):
        """Get interviews that need reminders"""
        return NotImplementedError
    
    @abstractmethod
    def mark_reminder_sent(self,interview_id:int):
        """Mark reminder as sent"""
        return NotImplementedError