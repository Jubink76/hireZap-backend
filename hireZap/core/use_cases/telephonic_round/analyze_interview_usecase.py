"""
core/use_cases/telephonic_round/analyze_interview_usecase.py
"""
from typing import Dict
from core.interface.telephonic_round_repository_port import TelephonicRoundRepositoryPort
from infrastructure.services.telephonic_service import (
    TranscriptionService,
    InterviewScorerService
)
from infrastructure.services.notification_service import NotificationService


class AnalyzeInterviewUseCase:
    """
    Analyze interview recording and generate performance scores
    This is the core AI processing use case
    """
    
    def __init__(
        self,
        repository: TelephonicRoundRepositoryPort,
        transcription_service: TranscriptionService,
        scorer_service: InterviewScorerService,
        notification_service: NotificationService
    ):
        self.repository = repository
        self.transcription_service = transcription_service
        self.scorer_service = scorer_service
        self.notification_service = notification_service
    
    def execute(
        self,
        interview_id: int,
        audio_file_path: str
    ) -> Dict:
        """
        Complete analysis pipeline:
        1. Transcribe audio
        2. Analyze with AI
        3. Generate scores
        4. Save results
        5. Send notifications
        
        Args:
            interview_id: Interview ID
            audio_file_path: Path to audio file
        
        Returns:
            {
                'success': bool,
                'interview_id': int,
                'overall_score': int,
                'decision': str,
                'transcription': str,
                'analysis': dict
            }
        """
        
        import time
        start_time = time.time()
        
        # 1. Get interview
        interview = self.repository.get_interview_by_id(interview_id)
        
        if not interview:
            return {
                'success': False,
                'error': 'Interview not found'
            }
        
        # 2. Get settings
        settings = self.repository.get_settings_by_id(interview.job_id)
        if not settings:
            settings = self.repository.create_default_settings(interview.job_id)
        
        try:
            # 3. Transcribe audio with Whisper
            print(f"📝 Starting transcription for interview {interview_id}...")
            
            with open(audio_file_path, 'rb') as audio_file:
                transcription_result = self.transcription_service.transcribe_audio(
                    audio_file=audio_file,
                    language='en'
                )
            
            if not transcription_result['success']:
                return {
                    'success': False,
                    'error': f"Transcription failed: {transcription_result.get('error')}"
                }
            
            # Save transcription to database
            transcription = self.repository.create_transcription(
                interview_id=interview_id,
                full_text=transcription_result['text'],
                segments=transcription_result['segments'],
                detected_language=transcription_result['language'],
                confidence=transcription_result.get('confidence')
            )
            
            print(f"✅ Transcription completed: {len(transcription_result['text'])} characters")
            
            # 4. Prepare job requirements
            job_requirements = {
                'job_title': interview.job.job_title,
                'required_skills': getattr(interview.job, 'skills_required', []) or [],
                'minimum_experience': getattr(interview.job, 'min_experience', 0) or 0,
                'responsibilities': getattr(interview.job, 'key_responsibilities', '') or ''
            }
            
            # 5. Prepare settings for AI scorer
            settings_dict = {
                'communication_weight': settings.communication_weight,
                'technical_knowledge_weight': settings.technical_knowledge_weight,
                'problem_solving_weight': settings.problem_solving_weight,
                'enthusiasm_weight': settings.enthusiasm_weight,
                'clarity_weight': settings.clarity_weight,
                'professionalism_weight': settings.professionalism_weight,
                'minimum_qualifying_score': settings.minimum_qualifying_score
            }
            
            # 6. Analyze with AI
            print(f"🤖 Starting AI analysis for interview {interview_id}...")
            
            analysis_result = self.scorer_service.analyze_interview(
                transcription=transcription_result['text'],
                job_requirements=job_requirements,
                settings=settings_dict
            )
            
            if not analysis_result['success']:
                return {
                    'success': False,
                    'error': f"AI analysis failed: {analysis_result.get('error')}"
                }
            
            print(f"✅ AI analysis completed")
            print(f"📊 Overall Score: {analysis_result['scores']['overall']}/100")
            print(f"✓ Decision: {analysis_result['decision']}")
            
            # 7. Save performance results
            performance_result = self.repository.save_performance_result(
                interview_id=interview_id,
                scores=analysis_result['scores'],
                decision=analysis_result['decision'],
                analysis=analysis_result['analysis']
            )
            
            # 8. Update application status based on decision
            self._update_application_status(
                interview=interview,
                decision=analysis_result['decision']
            )
            
            # 9. Calculate processing time
            processing_time = time.time() - start_time
            
            # 10. Send notifications
            self._send_completion_notifications(
                interview=interview,
                performance_result=performance_result
            )
            
            # 11. Trigger email notification
            self._trigger_result_email(interview_id)
            
            return {
                'success': True,
                'interview_id': interview_id,
                'overall_score': analysis_result['scores']['overall'],
                'decision': analysis_result['decision'],
                'transcription': transcription_result['text'][:500] + '...',  # Preview
                'analysis': analysis_result['analysis'],
                'processing_time': round(processing_time, 2),
                'message': 'Interview analyzed successfully'
            }
            
        except Exception as e:
            print(f"❌ Analysis failed for interview {interview_id}: {str(e)}")
            
            # Update interview status to failed
            self.repository.update_interview_status(
                interview_id=interview_id,
                status='failed'
            )
            
            return {
                'success': False,
                'error': f'Analysis failed: {str(e)}'
            }
    
    def _update_application_status(self, interview, decision: str):
        """Update application status based on interview decision"""
        application = interview.application
        
        if decision == 'qualified':
            application.current_stage_status = 'qualified'
            application.status = 'qualified'
        else:
            application.current_stage_status = 'rejected'
            application.status = 'rejected'
        
        application.save()
    
    def _send_completion_notifications(self, interview, performance_result):
        """Send WebSocket notifications about interview completion"""
        
        # Notify candidate
        self.notification_service.send_websocket_notification(
            user_id=interview.application.candidate_id,
            notification_type='interview_completed',
            data={
                'interview_id': interview.id,
                'job_title': interview.job.job_title,
                'score': performance_result.overall_score,
                'decision': performance_result.decision,
                'message': 'Your interview has been evaluated'
            }
        )
        
        # Notify recruiter
        if interview.conducted_by_id:
            self.notification_service.send_websocket_notification(
                user_id=interview.conducted_by_id,
                notification_type='interview_analyzed',
                data={
                    'interview_id': interview.id,
                    'candidate_name': f"{interview.application.first_name} {interview.application.last_name}",
                    'score': performance_result.overall_score,
                    'decision': performance_result.decision,
                    'job_title': interview.job.job_title
                }
            )
    
    def _trigger_result_email(self, interview_id: int):
        """Trigger Celery task to send result email"""
        from telephonic_round.tasks import send_interview_result_email
        
        send_interview_result_email.apply_async(
            args=[interview_id],
            countdown=10  # Wait 10 seconds
        )