from celery import shared_task
from django.utils import timezone
from infrastructure.repositories.telephonic_round_repository import TelephonicRoundRepository
from infrastructure.services.telephonic_service import (
    TranscriptionService,
    InterviewScorerService
)
from infrastructure.services.notification_service import NotificationService
from infrastructure.services.storage_factory import StorageFactory
import requests
import tempfile
import os


@shared_task(name='telephonic_round.send_interview_scheduled_email')
def send_interview_scheduled_email_task(interview_id: int):
    """
    Send email notification when interview is scheduled
    """
    try:
        repo = TelephonicRoundRepository()
        interview = repo.get_interview_by_id(interview_id)
        
        if not interview:
            return {'success': False, 'error': 'Interview not found'}
        
        # Email content
        candidate_name = f"{interview.application.first_name} {interview.application.last_name}"
        candidate_email = interview.application.email
        job_title = interview.job.job_title
        scheduled_time = interview.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
        duration = interview.scheduled_duration_minutes
        
        subject = f"Telephonic Interview Scheduled - {job_title}"
        
        message = f"""
Dear {candidate_name},

Your telephonic interview has been scheduled!

Job Position: {job_title}
Date & Time: {scheduled_time} ({interview.timezone})
Duration: {duration} minutes

Important Instructions:
1. Please be available at the scheduled time
2. Ensure you have a stable internet connection
3. Join from a quiet location
4. Keep your phone/device charged

{interview.scheduling_notes or ''}

You will receive a call link 5 minutes before the scheduled time.

Good luck!

Best regards,
Hiring Team
"""
        
        # Send email (implement your email service)
        # send_email(to=candidate_email, subject=subject, message=message)
        
        return {'success': True}
        
    except Exception as e:
        print(f"❌ Email sending failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='telephonic_round.send_interview_reminders')
def send_interview_reminders_task():
    """
    Celery beat task to send reminders for upcoming interviews
    Run every hour
    """
    try:
        repo = TelephonicRoundRepository()
        notification_service = NotificationService()
        
        # Get interviews that need reminders
        interviews = repo.get_upcoming_interviews_for_reminder(hours_before=24)
        
        sent_count = 0
        for interview in interviews:
            # Send WebSocket notification
            notification_service.send_websocket_notification(
                user_id=interview.application.candidate_id,
                notification_type='interview_reminder',
                data={
                    'interview_id': interview.id,
                    'job_title': interview.job.job_title,
                    'scheduled_at': interview.scheduled_at.isoformat(),
                    'duration': interview.scheduled_duration_minutes
                }
            )
            
            # Send email
            send_interview_reminder_email(interview)
            
            # Mark as sent
            repo.mark_reminder_sent(interview.id)
            sent_count += 1
        
        return {
            'success': True,
            'reminders_sent': sent_count
        }
        
    except Exception as e:
        print(f"❌ Reminder task failed: {str(e)}")
        return {'success': False, 'error': str(e)}


def send_interview_reminder_email(interview):
    """Send reminder email"""
    candidate_name = f"{interview.application.first_name} {interview.application.last_name}"
    candidate_email = interview.application.email
    job_title = interview.job.job_title
    scheduled_time = interview.scheduled_at.strftime('%B %d, %Y at %I:%M %p')
    
    subject = f"Reminder: Telephonic Interview Tomorrow - {job_title}"
    
    message = f"""
Dear {candidate_name},

This is a friendly reminder about your upcoming telephonic interview:

Job Position: {job_title}
Date & Time: {scheduled_time} ({interview.timezone})
Duration: {interview.scheduled_duration_minutes} minutes

Please ensure you're available and prepared.

Good luck!

Best regards,
Hiring Team
"""
    # send_email(to=candidate_email, subject=subject, message=message)


@shared_task(name='telephonic_round.process_interview_recording')
def process_interview_recording_task(call_session_id: str):
    """
    Process interview recording:
    1. Download recording from storage
    2. Transcribe using Whisper
    3. Analyze with AI
    4. Generate performance scores
    5. Send notifications
    """
    try:
        repo = TelephonicRoundRepository()
        transcription_service = TranscriptionService()
        scorer_service = InterviewScorerService()
        notification_service = NotificationService()
        
        # 1. Get call session
        session = repo.get_call_session_by_id(call_session_id)
        if not session:
            return {'success': False, 'error': 'Call session not found'}
        
        interview = session.interview
        
        # 2. Download recording
        recording_url = session.recording_url
        if not recording_url:
            return {'success': False, 'error': 'No recording URL'}
        
        # Download to temp file
        response = requests.get(recording_url, stream=True)
        response.raise_for_status()
        
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        try:
            for chunk in response.iter_content(chunk_size=8192):
                temp_file.write(chunk)
            temp_file.close()
            
            # 3. Transcribe audio
            print(f"📝 Starting transcription for interview {interview.id}...")
            with open(temp_file.name, 'rb') as audio_file:
                transcription_result = transcription_service.transcribe_audio(audio_file)
            
            if not transcription_result['success']:
                return {
                    'success': False,
                    'error': f"Transcription failed: {transcription_result.get('error')}"
                }
            
            # Save transcription
            transcription = repo.create_transcription(
                interview_id=interview.id,
                full_text=transcription_result['text'],
                segments=transcription_result['segments'],
                detected_language=transcription_result['language']
            )
            
            print(f"✅ Transcription completed for interview {interview.id}")
            
            # 4. Get job requirements and settings
            settings = repo.get_settings_by_job(interview.job_id)
            if not settings:
                settings = repo.create_default_settings(interview.job_id)
            
            job_requirements = {
                'job_title': interview.job.job_title,
                'required_skills': interview.job.skills_required or [],
                'minimum_experience': interview.job.min_experience or 0,
                'responsibilities': interview.job.key_responsibilities or ''
            }
            
            settings_dict = {
                'communication_weight': settings.communication_weight,
                'technical_knowledge_weight': settings.technical_knowledge_weight,
                'problem_solving_weight': settings.problem_solving_weight,
                'enthusiasm_weight': settings.enthusiasm_weight,
                'clarity_weight': settings.clarity_weight,
                'professionalism_weight': settings.professionalism_weight,
                'minimum_qualifying_score': settings.minimum_qualifying_score
            }
            
            # 5. Analyze interview
            print(f"🤖 Starting AI analysis for interview {interview.id}...")
            analysis_result = scorer_service.analyze_interview(
                transcription=transcription_result['text'],
                job_requirements=job_requirements,
                settings=settings_dict
            )
            
            if not analysis_result['success']:
                return {
                    'success': False,
                    'error': f"Analysis failed: {analysis_result.get('error')}"
                }
            
            # 6. Save performance results
            performance = repo.save_performance_result(
                interview_id=interview.id,
                scores=analysis_result['scores'],
                decision=analysis_result['decision'],
                analysis=analysis_result['analysis']
            )
            
            print(f"✅ Analysis completed for interview {interview.id}")
            print(f"📊 Score: {performance.overall_score}/100 - Decision: {performance.decision}")
            
            # 7. Update application status
            application = interview.application
            application.current_stage_status = (
                'qualified' if performance.decision == 'qualified' else 'rejected'
            )
            application.save()
            
            # 8. Send notifications
            # To recruiter
            notification_service.send_websocket_notification(
                user_id=interview.conducted_by_id,
                notification_type='interview_analyzed',
                data={
                    'interview_id': interview.id,
                    'candidate_name': interview.candidate_name,
                    'score': performance.overall_score,
                    'decision': performance.decision
                }
            )
            
            # To candidate
            notification_service.send_websocket_notification(
                user_id=interview.application.candidate_id,
                notification_type='interview_completed',
                data={
                    'interview_id': interview.id,
                    'job_title': interview.job.job_title,
                    'decision': performance.decision
                }
            )
            
            # Send email to candidate
            send_interview_result_email.delay(interview.id)
            
            return {
                'success': True,
                'interview_id': interview.id,
                'score': performance.overall_score,
                'decision': performance.decision
            }
            
        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file.name)
            except:
                pass
        
    except Exception as e:
        print(f"❌ Recording processing failed: {str(e)}")
        return {'success': False, 'error': str(e)}


@shared_task(name='telephonic_round.send_interview_result_email')
def send_interview_result_email(interview_id: int):
    """Send interview result email to candidate"""
    try:
        repo = TelephonicRoundRepository()
        interview = repo.get_interview_by_id(interview_id)
        
        if not interview or not hasattr(interview, 'performance_result'):
            return {'success': False, 'error': 'Interview or result not found'}
        
        performance = interview.performance_result
        candidate_name = interview.candidate_name
        candidate_email = interview.application.email
        job_title = interview.job.job_title
        
        if performance.final_decision == 'qualified':
            subject = f"Good News! You're Moving Forward - {job_title}"
            message = f"""
Dear {candidate_name},

Congratulations! We're pleased to inform you that you've successfully passed the telephonic interview round for the {job_title} position.

Your Performance:
- Overall Score: {performance.final_score}/100
- Decision: Qualified for Next Round

Summary: {performance.ai_summary}

Our team will contact you soon regarding the next steps in the interview process.

Best regards,
Hiring Team
"""
        else:
            subject = f"Interview Update - {job_title}"
            message = f"""
Dear {candidate_name},

Thank you for taking the time to interview for the {job_title} position.

After careful evaluation, we've decided not to move forward with your application at this time.

Your Performance:
- Overall Score: {performance.final_score}/100

We appreciate your interest in our company and wish you the best in your job search.

Best regards,
Hiring Team
"""
        
        # send_email(to=candidate_email, subject=subject, message=message)
        
        return {'success': True}
        
    except Exception as e:
        print(f"❌ Result email failed: {str(e)}")
        return {'success': False, 'error': str(e)}