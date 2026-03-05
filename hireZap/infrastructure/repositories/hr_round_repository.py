from typing import List, Optional, Dict
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import uuid

from hr_round.models import(
    HRInterview,
    HRRoundSettings,
    MeetingSession,
    InterviewRecording,
    InterviewNotes,
    InterviewChatMessage,
    InterviewResult
)
from application.models import ApplicationModel
from job.models import JobModel
from core.interface.hr_round_repository_port import HRRoundRepositoryPort
import logging
logger = logging.getLogger(__name__)
class HRInterviewRepository(HRRoundRepositoryPort):

    #Settings
    
    def get_settings_by_id(self,job_id:int) ->Optional[HRRoundSettings]:
        try:
            return HRRoundSettings.objects.get(job_id=job_id)
        except HRRoundSettings.DoesNotExist:
            return None
    
    def create_default_settings(self,job_id:int) ->HRRoundSettings:
        return HRRoundSettings.objects.create(job_id = job_id)
    
    def update_settings(self, job_id:int, settings_data:Dict) -> HRRoundSettings:
        settings, created = HRRoundSettings.objects.update_or_create(
            job_id= job_id,
            defaults = settings_data
        )
        return settings
      #Interviews
    
    def create_interview(self,
                         application_id:int,
                         job_id:int,
                         stage_id:int=None,
                         ) -> HRInterview:
        return HRInterview.objects.create(
            application_id_id=application_id,
            job_id =job_id,
            stage_id=stage_id
        )
    
    def get_interview_by_id(self, interview_id: int) -> Optional[HRInterview]:
        """Get interview by ID"""
        try:
            return HRInterview.objects.select_related(
                'application',
                'job',
                'job__company',
                'stage',
                'conducted_by'
            ).prefetch_related(
                'notes',
                'result',
                'recording',
            ).get(id=interview_id)
        except HRInterview.DoesNotExist:
            return None
    
    def get_interview_by_application(self, application_id: int) -> Optional[HRInterview]:
        """Get interview by application"""
        try:
            return HRInterview.objects.select_related(
                'application',
                'job',
                'stage'
            ).get(application_id=application_id)
        except HRInterview.DoesNotExist:
            return None
    
    def list_interviews_by_job(
        self,
        job_id: int,
        status: str = None) -> List[HRInterview]:
        """List interviews for a job"""
        queryset = HRInterview.objects.filter(job_id=job_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related(
            'application',
            'job',
            'stage',
            'conducted_by'
        ).order_by('-scheduled_at')
    
    def list_interviews_by_recruiter(
        self,
        recruiter_id: int,
        status: str = None) -> List[HRInterview]:
        """List interviews conducted by recruiter"""
        queryset = HRInterview.objects.filter(conducted_by_id=recruiter_id)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.select_related(
            'application',
            'job',
            'stage'
        ).order_by('-scheduled_at')
    
    @transaction.atomic
    def schedule_interview(
        self,
        application_id: int,
        scheduled_at: timezone.datetime,
        duration_minutes: int,
        timezone_str: str,
        conducted_by_id: int,
        scheduling_notes: str = None) -> HRInterview:
        """Schedule an HR interview"""
        # Get or create interview
        application = ApplicationModel.objects.get(id=application_id)
        interview, created = HRInterview.objects.get_or_create(
            application_id=application_id,
            defaults={
                'job_id': application.job_id,
                'stage_id': application.current_stage_id
            }
        )
    
        # Update interview
        interview.scheduled_at = scheduled_at
        interview.scheduled_duration_minutes = duration_minutes
        interview.timezone = timezone_str
        interview.conducted_by_id = conducted_by_id
        interview.scheduling_notes = scheduling_notes
        interview.status = 'scheduled'
        interview.save()
        
        # Update application status
        application.status = 'interview_scheduled'
        application.interview_date = scheduled_at
        application.save()
        
        return interview
    
    @transaction.atomic
    def bulk_schedule_interviews(
        self,
        application_ids: List[int],
        scheduled_at: timezone.datetime,
        duration_minutes: int,
        timezone_str: str,
        conducted_by_id: int,
        scheduling_notes: str = None) -> List[HRInterview]:
        """Schedule multiple interviews at once"""
        
        interviews = []
        for app_id in application_ids:
            interview = self.schedule_interview(
                application_id=app_id,
                scheduled_at=scheduled_at,
                duration_minutes=duration_minutes,
                timezone_str=timezone_str,
                conducted_by_id=conducted_by_id,
                scheduling_notes=scheduling_notes
            )
            interviews.append(interview)
        
        return interviews
    
    def update_interview_status(
        self,
        interview_id: int,
        status: str,
        **kwargs) -> HRInterview:
        """Update interview status"""
        interview = self.get_interview_by_id(interview_id)
        interview.status = status
        
        # Update timestamps based on status
        if status == 'in_progress' and not interview.started_at:
            interview.started_at = timezone.now()
        elif status == 'completed' and not interview.ended_at:
            interview.ended_at = timezone.now()
            # Calculate actual duration
            if interview.started_at:
                duration = (interview.ended_at - interview.started_at).total_seconds() / 60
                interview.actual_duration_minutes = int(duration)
        
        # Handle additional kwargs
        for key, value in kwargs.items():
            setattr(interview, key, value)
        
        interview.save()
        return interview
    
    def cancel_interview(
        self,
        interview_id: int,
        reason: str) -> HRInterview:
        """Cancel interview"""
        interview = self.get_interview_by_id(interview_id)
        interview.status = 'cancelled'
        interview.cancellation_reason = reason
        interview.save()
        
        # Update application status
        application = interview.application
        application.status = 'under_review'
        application.save()
        
        return interview
    
    def mark_notification_sent(self, interview_id: int):
        """Mark notification as sent"""
        HRInterview.objects.filter(id=interview_id).update(
            notification_sent=True
        )
    
    def mark_email_sent(self, interview_id: int):
        """Mark email as sent"""
        HRInterview.objects.filter(id=interview_id).update(
            email_sent=True
        )
    
    def mark_reminder_sent(self, interview_id: int):
        """Mark reminder as sent"""
        HRInterview.objects.filter(id=interview_id).update(
            reminder_sent=True
        )
    
    def get_upcoming_interviews_for_reminder(
        self,
        hours_before: int = 24) -> List[HRInterview]:
        """Get interviews that need reminders"""
        now = timezone.now()
        target_time = now + timedelta(hours=hours_before)
        
        return HRInterview.objects.filter(
            status='scheduled',
            scheduled_at__lte=target_time,
            scheduled_at__gte=now,
            reminder_sent=False
        ).select_related('application', 'job')
    
    #Meeting Sessions
    
    def create_meeting_session(
        self,
        interview_id: int,
        recruiter_id: str,
        candidate_id: str) -> MeetingSession:
        """Create meeting session"""
        session_id = str(uuid.uuid4())
        room_id = f"hr-{interview_id}-{uuid.uuid4().hex[:8]}"
        
        from infrastructure.services.hr_round_service import MeetingService
        zegocloud_token = MeetingService.generate_zegocloud_token(
            user_id=recruiter_id,
            room_id=room_id
        )
        return MeetingSession.objects.create(
            interview_id=interview_id,
            session_id=session_id,
            room_id=room_id,
            zegocloud_room_id=room_id,
            recruiter_id=recruiter_id,
            candidate_id=candidate_id
        )
    
    def get_meeting_session(self, session_id: str) -> Optional[MeetingSession]:
        """Get meeting session by session ID"""
        try:
            return MeetingSession.objects.select_related('interview').get(
                session_id=session_id
            )
        except MeetingSession.DoesNotExist:
            return None
    
    def get_meeting_session_by_interview(
        self,
        interview_id: int) -> Optional[MeetingSession]:
        """Get meeting session by interview"""
        try:
            return MeetingSession.objects.get(interview_id=interview_id)
        except MeetingSession.DoesNotExist:
            return None
    
    def update_participant_connection(
        self,
        session_id: str,
        participant_type: str,
        connected: bool) -> MeetingSession:
        """Update participant connection status"""
        session = self.get_meeting_session(session_id)
        
        if participant_type == 'recruiter':
            session.recruiter_connected = connected
            if connected and not session.recruiter_joined_at:
                session.recruiter_joined_at = timezone.now()
        elif participant_type == 'candidate':
            session.candidate_connected = connected
            if connected and not session.candidate_joined_at:
                session.candidate_joined_at = timezone.now()
                # Update interview status
                interview = session.interview
                interview.status = 'candidate_joined'
                interview.candidate_joined_at = timezone.now()
                interview.save()
        
        session.save()
        return session
    
    def delete_meeting_session(self, session_id:str):
        try:
            MeetingSession.objects.filter(session_id=session_id).delete()
        except MeetingSession.DoesNotExist:
            return None

        
    
    # def start_recording(self, session_id: str) -> MeetingSession:
    #     """Start recording"""
    #     session = self.get_meeting_session(session_id)
    #     session.is_recording = True
    #     session.recording_started_at = timezone.now()
    #     session.save()
    #     return session
    
    # def stop_recording(self, session_id: str) -> MeetingSession:
    #     """Stop recording"""
    #     session = self.get_meeting_session(session_id)
    #     session.is_recording = False
    #     session.recording_stopped_at = timezone.now()
    #     session.save()
    #     return session
    
    def end_meeting_session(self, session_id: str) -> MeetingSession:
        """End meeting session"""
        session = self.get_meeting_session(session_id)
        session.ended_at = timezone.now()
        session.recruiter_connected = False
        session.candidate_connected = False
        
        # Auto-stop recording if still recording
        if session.is_recording and not session.recording_stopped_at:
            session.is_recording = False
            session.recording_stopped_at = timezone.now()
        
        session.save()
        
        # Update interview status
        interview = session.interview
        if interview.status != 'completed':
            interview.status = 'completed'
            interview.ended_at = timezone.now()
            if interview.started_at:
                duration = (interview.ended_at - interview.started_at).total_seconds() / 60
                interview.actual_duration_minutes = int(duration)
            interview.save()
        
        return session
    
    #Recordings
    
    def create_recording(
        self,
        interview_id: int,
        video_url: str,
        video_key: str,
        duration_seconds: int = None,
        file_size_bytes: int = None,
        resolution: str = None) -> InterviewRecording:

        recording, created = InterviewRecording.objects.update_or_create(
            interview_id=interview_id,
            defaults={
                'video_url': video_url,
                'video_key': video_key,
                'duration_seconds': duration_seconds,
                'file_size_bytes': file_size_bytes,
                'resolution': resolution,
                'processing_status': 'completed',
                'upload_completed_at': timezone.now()
            }
        )
        return recording
    def save_zegocloud_recording(
        self,
        session_id: str,
        recording_url: str,
        recording_id: str) -> MeetingSession:
        """Save recording URL from ZegoCloud webhook"""
        session = self.get_meeting_session(session_id)
        session.zegocloud_recording_url = recording_url
        session.zegocloud_recording_id = recording_id
        session.save()
        return session
    
    def update_recording_thumbnail(
        self,
        interview_id: int,
        thumbnail_url: str,
        thumbnail_key: str) -> InterviewRecording:
        """Update recording thumbnail"""
        recording = InterviewRecording.objects.get(interview_id=interview_id)
        recording.thumbnail_url = thumbnail_url
        recording.thumbnail_key = thumbnail_key
        recording.save()
        return recording
    
    def get_recording_by_interview(
        self,
        interview_id: int) -> Optional[InterviewRecording]:
        """Get recording by interview"""
        try:
            return InterviewRecording.objects.get(interview_id=interview_id)
        except InterviewRecording.DoesNotExist:
            return None
    
    #Notes
    
    def create_or_update_notes(
        self,
        interview_id: int,
        recorded_by_id: int,
        notes_data: Dict) -> InterviewNotes:
        """Create or update interview notes"""
        notes, created = InterviewNotes.objects.update_or_create(
            interview_id=interview_id,
            defaults={
                'recorded_by_id': recorded_by_id,
                **notes_data
            }
        )
        
        # Calculate weighted score
        calculated = notes.calculate_weighted_score()
        if calculated is not None:
            notes.calculated_score = calculated
            notes.save()
        
        return notes
    
    def get_notes_by_interview(self, interview_id: int) -> Optional[InterviewNotes]:
        """Get notes by interview"""
        try:
            return InterviewNotes.objects.select_related(
                'interview',
                'recorded_by'
            ).get(interview_id=interview_id)
        except InterviewNotes.DoesNotExist:
            return None
    
    def finalize_notes(self, interview_id: int) -> InterviewNotes:
        """Finalize notes"""
        notes = self.get_notes_by_interview(interview_id)
        notes.is_finalized = True
        notes.finalized_at = timezone.now()
        notes.save()
        return notes
    
    #Chat Messages
    
    # def save_chat_message(
    #     self,
    #     interview_id: int,
    #     sender_id: str,
    #     sender_type: str,
    #     message: str,
    #     is_system_message: bool = False) -> InterviewChatMessage:
    #     """Save chat message to database"""
    #     return InterviewChatMessage.objects.create(
    #         interview_id=interview_id,
    #         sender_id=sender_id,
    #         sender_type=sender_type,
    #         message=message,
    #         is_system_message=is_system_message
    #     )
    
    # def get_chat_messages(
    #     self,
    #     interview_id: int,
    #     limit: int = 100) -> List[InterviewChatMessage]:
    #     """Get chat messages for interview"""
    #     return InterviewChatMessage.objects.filter(
    #         interview_id=interview_id
    #     ).order_by('-sent_at')[:limit]
    def save_zegocloud_chat_message(
        self,
        interview_id: int,
        message_data: dict) -> InterviewChatMessage:
        """Save chat message from ZegoCloud webhook"""
        return InterviewChatMessage.objects.create(
            interview_id=interview_id,
            zegocloud_message_id=message_data.get('message_id'),
            sender_id=message_data.get('sender_id'),
            sender_type=message_data.get('sender_type'),
            message=message_data.get('message'),
            message_type=message_data.get('type', 'text')
        )
    def delete_chat_messages(self, interview_id: int):
        """Delete all chat messages for interview"""
        InterviewChatMessage.objects.filter(interview_id=interview_id).delete()
    
    #Results
    
    def create_or_update_result(
        self,
        interview_id: int,
        final_score: int,
        decision: str,
        decided_by_id: int,
        decision_reason: str = None,
        next_steps: str = None) -> InterviewResult:
        """Create or update interview result"""
        result, created = InterviewResult.objects.update_or_create(
            interview_id=interview_id,
            defaults={
                'final_score': final_score,
                'decision': decision,
                'decision_reason': decision_reason,
                'next_steps': next_steps,
                'decided_by_id': decided_by_id,
                'decided_at': timezone.now()
            }
        )
        return result
    
    def get_result_by_interview(self, interview_id: int) -> Optional[InterviewResult]:
        """Get result by interview"""
        try:
            return InterviewResult.objects.select_related(
                'interview',
                'decided_by'
            ).get(interview_id=interview_id)
        except InterviewResult.DoesNotExist:
            return None
        
    def move_to_next_stage(self, interview_ids: List[int], feedback: str = '') -> int:
        from selection_process.models import SelectionProcessModel
        from application.models import ApplicationStageHistory

        moved_count = 0

        for interview_id in interview_ids:
            try:
                interview = self.get_interview_by_id(interview_id)
                result    = self.get_result_by_interview(interview_id)

                if not interview or not result:
                    continue

                application = interview.application

                current_process = SelectionProcessModel.objects.get(
                    job=interview.job,
                    stage=interview.stage
                )

                next_process = SelectionProcessModel.objects.filter(
                    job=interview.job,
                    order__gt=current_process.order,
                    is_active=True
                ).order_by('order').first()

                if not next_process:
                    logger.warning(f"No next stage found for interview {interview_id}")
                    continue

                next_stage = next_process.stage

                stage_after_next = SelectionProcessModel.objects.filter(
                    job=interview.job,
                    order__gt=next_process.order,
                    is_active=True
                ).exists()

                new_status = 'shortlisted' if not stage_after_next else 'qualified'

                application.current_stage        = next_stage
                application.current_stage_status = 'started'
                application.status               = new_status
                application.save(update_fields=[
                    'current_stage', 'current_stage_status', 'status', 'updated_at'
                ])

                ApplicationStageHistory.objects.update_or_create(
                    application=application,
                    stage=interview.stage,
                    defaults={
                        'status':'qualified',
                        'feedback':f'HR Interview Score: {result.final_score}/100. {feedback}'.strip('. '),
                        'completed_at': timezone.now(),
                    }
                )

                ApplicationStageHistory.objects.update_or_create(
                    application=application,
                    stage=next_stage,
                    defaults={ 
                        'status':'started',
                        'feedback':     None,
                        'completed_at': None,
                    }
                )

                moved_count += 1

            except Exception as e:
                logger.error(f"Failed to move interview {interview_id}: {str(e)}")
                continue

        return moved_count