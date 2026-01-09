from typing import List, Dict, Optional
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from django.db.models import Q, Prefetch, F
from telephonic_round.models import(
    TelephonicInterview,
    TelephonicRoundSettings,
    CallSession,
    InterviewTranscription,
    InterviewPerformanceResult,
    InterviewFeedback
)
from application.models import ApplicationModel
from job.models import JobModel
from django.utils import timezone

class TelephonicRoundRepository(TelephonicRoundRepositoryPort):

    #settings
    def get_settings_by_id(self, job_id:int) -> Optional[TelephonicRoundSettings]:
        try:
            return TelephonicRoundSettings.objects.select_related('job').get(job_id=job_id)
        except TelephonicRoundSettings.DoesNotExist:
            return None
        
    def create_default_settings(self,job_id:int) -> TelephonicRoundSettings:
        return TelephonicRoundSettings.objects.create(job_id=job_id)
    
    def update_settings(self,job_id:int, settings_data:Dict) -> TelephonicRoundSettings:
        settings, created = TelephonicRoundSettings.objects.update_or_create(
            job_id=job_id,
            defaults=settings_data
        )
        return settings
    
    #inerviews
    def get_interview_by_id(self, interview_id:int) ->Optional[TelephonicInterview]:
        try:
            return TelephonicInterview.objects.select_related(
                'application',
                'application__candidate',
                'job',
                'stage',
                'conducted_by'
            ).prefetch_related(
                'call_session',
                'transcription',
                'performance_result'
            ).get(id=interview_id)
        except TelephonicInterview.DoesNotExist:
            return None
        
    def get_interview_by_application(self,application_id:int) -> Optional[TelephonicInterview]:
        try:
            return TelephonicInterview.objects.select_related(
                'application',
                'job',
                'stage'
            ).prefetch_related(
                'call_session',
                'transcription',
                'performance_result'
            ).get(application_id=application_id)
        except TelephonicInterview.DoesNotExist:
            return None
        
    def get_interviews_by_job(self, job_id:int, status:Optional[str]=None)-> List[TelephonicInterview]:
        queryset = TelephonicInterview.objects.select_related(
            'application',
            'application__candidate',
            'application__current_stage',
            'job',
            'stage'
        ).prefetch_related(
            'call_session',
            'transcription',
            'performance_result'
        ).filter(job_id=job_id)

        if status:
            queryset = queryset.filter(status = status)
        
        return list(queryset.order_by('scheduled_at'))
    
    def candidate_for_telephonic_round(self, job_id:int, stage_id:Optional[int]=None) -> List[ApplicationModel]:
        queryset = ApplicationModel.objects.select_related(
            'candidate',
            'candidate__user',
            'current_stage',
            'job'
        ).filter(
            job_id=job_id,
            current_stage_status='qualified'
        )

        if stage_id:
            queryset = queryset.filter(current_stage_id=stage_id)

        return list(queryset)
    

    def get_unscheduled_interviews(self, job_id:int) -> List[ApplicationModel]:

        return list(
            TelephonicInterview.objects.select_related('application').filter(
                job_id=job_id,
                status = 'not_scheduled'
            ).order_by('created_at')
        )
    
    def get_scheduled_interviews(self, job_id:int, upcoming_only:bool=False) -> List[ApplicationModel]:

        queryset = TelephonicInterview.objects.select_related(
            'application','' \
            'application__candidate'
        ).filter(
            job_id=job_id,
            status='scheduled'
        )

        if upcoming_only:
            queryset = queryset.filter(scheduled_at__gte=timezone.now())

        return list(queryset.order_by('scheduled_at'))
    
    def get_completed_interviews(self, job_id:int) -> List[ApplicationModel]:

        return list(
            TelephonicInterview.objects.select_related(
                'application',
                'performance_result'
            ).filter(
                job_id=job_id,
                status='completed'
            ).order_by('-ended_at')
        )

    # create/ update interview

    def create_interview(self, application_id:int, **kwargs) -> TelephonicInterview:

        application = ApplicationModel.objects.select_related(
            'job',
            'current_stage'
        ).get(id=application_id)

        return TelephonicInterview.objects.create(
            application_id=application_id,
            job_id = application.job_id,
            stage_id = application.current_stage_id,
            **kwargs
        )
    
    def update_interview_status(self,interview_id:int, status:str, **kwargs) -> TelephonicInterview:
        interview = TelephonicInterview.objects.get(id=interview_id)
        interview_status = status

        for key, value in kwargs.items():
            setattr(interview, key,value)
        
        interview.save()
        return interview
    
    def schedule_interview(
            self,
            interview_id:int,
            scheduled_at,
            duration:int,
            timezone:str,
            notes:Optional[str]=None
    )-> TelephonicInterview:
        
        interview = TelephonicInterview.objects.get(id=interview_id)
        interview.scheduled_at= scheduled_at
        interview.scheduled_duration_minutes = duration
        interview.timezone = timezone
        interview.scheduling_notes = notes
        interview.status = 'scheduled'
        interview.save()
        return interview
    
    def bulk_create_interview(self,applications:List[ApplicationModel]) -> List[TelephonicInterview]:

        interviews = []
        for app in applications:
            interviews.append(
                TelephonicInterview(
                    application_id=app.id,
                    job_id=app.job_id,
                    stage_id=app.current_stage_id,
                    status ='not_scheduled'
                )
            )

            return TelephonicInterview.objects.bulk_create(
                interviews,
                ignore_conflicts=True
            )
        
    #call session

    def create_call_session(
            self,
            interview_id: int,
            session_id: str,
            caller_id: str,
            callee_id: str
        ) -> CallSession:
        return CallSession.objects.create(
            interview_id=interview_id,
            session_id=session_id,
            caller_id=caller_id,
            callee_id=callee_id,
            is_recording=True
        )
    
    def get_call_session_by_id(self, session_id: str) -> Optional[CallSession]:

        try:
            return CallSession.objects.select_related('interview').get(session_id=session_id)
        except CallSession.DoesNotExist:
            return None
        
    def update_call_session(
        self,
        session_id: str,
        **kwargs
    ) -> CallSession:
        session = CallSession.objects.get(session_id=session_id)
        
        for key, value in kwargs.items():
            setattr(session, key, value)
        
        session.save()
        return session
    
    def end_call_session(
        self,
        session_id: str,
        recording_url: str,
        recording_key: str,
        duration_seconds: int,
        recording_size_bytes: int
    ) -> CallSession:
        session = CallSession.objects.get(session_id=session_id)
        session.ended_at = timezone.now()
        session.recording_url = recording_url
        session.recording_key = recording_key
        session.recording_duration_seconds = duration_seconds
        session.recording_size_bytes = recording_size_bytes
        session.is_recording = False
        session.save()
        return session
    
    def create_transcription(
        self,
        interview_id: int,
        full_text: str,
        segments: List[Dict],
        detected_language: str = 'en',
        confidence: Optional[float] = None
    ) -> InterviewTranscription:
        
        return InterviewTranscription.objects.create(
            interview_id=interview_id,
            full_text=full_text,
            segments=segments,
            detected_language=detected_language,
            confidence=confidence,
            processing_status='completed'
        )
    
    def update_transcription_status(
        self,
        interview_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> InterviewTranscription:
        transcription = InterviewTranscription.objects.get(interview_id=interview_id)
        transcription.processing_status = status
        if error_message:
            transcription.error_message = error_message
        transcription.save()
        return transcription
    
    def save_performance_result(
        self,
        interview_id: int,
        scores: Dict,
        decision: str,
        analysis: Dict
    ) -> InterviewPerformanceResult:
        result, created = InterviewPerformanceResult.objects.update_or_create(
            interview_id=interview_id,
            defaults={
                'overall_score': scores['overall'],
                'communication_score': scores['communication'],
                'technical_knowledge_score': scores['technical_knowledge'],
                'problem_solving_score': scores['problem_solving'],
                'enthusiasm_score': scores['enthusiasm'],
                'clarity_score': scores['clarity'],
                'professionalism_score': scores['professionalism'],
                'decision': decision,
                'ai_summary': analysis.get('summary'),
                'key_highlights': analysis.get('highlights', []),
                'areas_for_improvement': analysis.get('improvements', []),
                'technical_assessment': analysis.get('technical'),
                'communication_assessment': analysis.get('communication'),
                'key_topics_discussed': analysis.get('topics', []),
                'questions_asked_count': analysis.get('questions_count', 0),
            }
        )
        return result
    
    def update_manual_score(
        self,
        interview_id: int,
        manual_score: int,
        manual_decision: str,
        override_reason: str,
        overridden_by_id: int
    ) -> InterviewPerformanceResult:
        result = InterviewPerformanceResult.objects.get(interview_id=interview_id)
        result.manual_score_override = manual_score
        result.manual_decision_override = manual_decision
        result.override_reason = override_reason
        result.overridden_by_id = overridden_by_id
        result.overridden_at = timezone.now()
        result.save()
        return result
    
    def get_performance_result(self, interview_id: int) -> Optional[InterviewPerformanceResult]:
        """Get performance result"""
        try:
            return InterviewPerformanceResult.objects.select_related('interview').get(
                interview_id=interview_id
            )
        except InterviewPerformanceResult.DoesNotExist:
            return None
        
    def get_job_interview_stats(self, job_id: int) -> Dict:
        interviews = TelephonicInterview.objects.filter(job_id=job_id)
        
        total = interviews.count()
        not_scheduled = interviews.filter(status='not_scheduled').count()
        scheduled = interviews.filter(status='scheduled').count()
        completed = interviews.filter(status='completed').count()
        
        # Get qualified count from performance results
        qualified = InterviewPerformanceResult.objects.filter(
            interview__job_id=job_id,
            decision='qualified'
        ).count()
        
        # Average score
        from django.db.models import Avg
        avg_score = InterviewPerformanceResult.objects.filter(
            interview__job_id=job_id
        ).aggregate(avg=Avg('overall_score'))['avg'] or 0
        
        return {
            'total_candidates': total,
            'not_scheduled': not_scheduled,
            'scheduled': scheduled,
            'completed': completed,
            'qualified': qualified,
            'average_score': round(avg_score, 2)
        }
    
    def move_interviews_to_next_stage(self,interview_ids: List[int],feedback: str = '') -> int:
        from application.models import ApplicationStageHistory
        from selection_process.models import SelectionProcessModel
        
        moved_count = 0
        
        for interview_id in interview_ids:
            interview = self.get_interview_by_id(interview_id)
            if not interview:
                continue
            
            application = interview.application
            current_stage = application.current_stage
            
            # Get next stage
            next_stage_process = SelectionProcessModel.objects.filter(
                job_id=interview.job_id,
                order__gt=current_stage.order if current_stage else 0,
                is_active=True
            ).order_by('order').first()
            
            if not next_stage_process:
                continue
            
            # Update application
            application.current_stage = next_stage_process.stage
            application.current_stage_status = 'pending'
            application.status = 'qualified'
            application.save()
            
            # Create history record
            ApplicationStageHistory.objects.create(
                application=application,
                stage=next_stage_process.stage,
                status='started',
                feedback=feedback or 'Passed telephonic round'
            )
            
            moved_count += 1
        
        return moved_count
    
    def get_upcoming_interviews_for_reminder(self, hours_before: int = 24) -> List[TelephonicInterview]:
        """Get interviews that need reminders"""
        from datetime import timedelta
        now = timezone.now()
        target_time = now + timedelta(hours=hours_before)
        
        return list(
            TelephonicInterview.objects.filter(
                status='scheduled',
                scheduled_at__lte=target_time,
                scheduled_at__gte=now,
                reminder_sent=False
            ).select_related('application')
        )
    
    def mark_reminder_sent(self, interview_id: int):
        """Mark reminder as sent"""
        TelephonicInterview.objects.filter(id=interview_id).update(
            reminder_sent=True
        )