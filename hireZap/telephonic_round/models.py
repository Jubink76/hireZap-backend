from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator 
from job.models import  JobModel
from application.models import ApplicationModel
from selection_process.models import SelectionStageModel

class TelephonicRoundSettings(models.Model):
    job = models.OneToOneField(
        JobModel,
        on_delete=models.CASCADE,
        related_name='telephonic_settings'
    )
    #scoring weights
    communication_weight = models.IntegerField(default=30)
    technical_knowledge_weight = models.IntegerField(default=25)
    problem_solving_weight = models.IntegerField(default=20)
    enthusiasm_weight = models.IntegerField(default=10)
    clarity_weight = models.IntegerField(default=10)
    professionalism_weight = models.IntegerField(default=5)

    #threshold
    minimum_qualifying_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    #Interview settings
    default_duration_minutes = models.IntegerField(default=30)
    auto_schedule_enabled = models.BooleanField(default=False)
    send_reminders = models.BooleanField(default=True)
    reminder_hours_before = models.IntegerField(default=24)

    #Recording settings
    enable_recording = models.BooleanField(default=True)
    enable_transcription = models.BooleanField(default=True)
    enable_ai_analysis = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'telephonic_round_settings'
    
    def __str__(self):
        return f"Telephonic settings -{self.job.job_title}"
    

class TelephonicInterview(models.Model):
    """Complete interview handling"""
    STATUS_CHOICES = [
        ('not_scheduled','Not Scheduled'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
        ('failed', 'Failed'),
    ]
    application = models.OneToOneField(
        ApplicationModel,
        on_delete=models.CASCADE,
        related_name='telephonic_interview'
    )
    job = models.ForeignKey(
        JobModel,
        on_delete=models.CASCADE,
        related_name='telephonic_interviews',
    )
    stage = models.ForeignKey(
        SelectionStageModel,
        on_delete=models.CASCADE,
        related_name='telephonic_interviews',
        null=True,
        blank=True
    )

    #scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_duration_minutes = models.IntegerField(default=30)
    timezone = models.CharField(max_length=100, default='Asia/Kolkata')

    #status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_scheduled',
        db_index=True
    )

    #timing
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)

    #Notes
    interviewer_notes = models.TextField(blank=True, null=True)
    scheduling_notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)

    #Notifications
    notification_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)

    #conducted by
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_interviews'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now = True)

    class Meta:
        db_table = 'telephonic_interviews'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['application', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['status', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"Interview - {self.application.first_name} {self.application.last_name} - {self.status}"
    
    @property
    def candidate_name(self):
        return f"{self.application.first_name} {self.application.last_name}"
    
    @property
    def is_upcoming(self):
        """Check if interview is upcoming (within next 5 mins)"""
        if not self.scheduled_at or self.status != 'scheduled':
            return False
        from django.utils import timezone
        from datetime import timedelta
        now = timezone.now()
        return now <= self.scheduled_at <= now + timedelta(minutes=5)
    
class CallSession(models.Model):
    """ WebRTC call session tracking"""
    
    interview = models.OneToOneField(
        TelephonicInterview,
        on_delete=models.CASCADE,
        related_name='call_session'
    )
    
    # Session identifiers
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    peer_connection_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Call details
    caller_id = models.CharField(max_length=100)  # Recruiter ID
    callee_id = models.CharField(max_length=100)  # Candidate ID
    
    # Connection info
    connection_quality = models.CharField(
        max_length=20,
        choices=[
            ('excellent', 'Excellent'),
            ('good', 'Good'),
            ('fair', 'Fair'),
            ('poor', 'Poor'),
        ],
        default='good'
    )
    
    # Recording
    is_recording = models.BooleanField(default=False)
    recording_url = models.URLField(max_length=1024, blank=True, null=True)
    recording_key = models.CharField(max_length=500, blank=True, null=True)
    recording_duration_seconds = models.IntegerField(null=True, blank=True)
    recording_size_bytes = models.BigIntegerField(null=True, blank=True)
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'call_sessions'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['interview']),
        ]
    
    def __str__(self):
        return f"Call Session {self.session_id} - {self.interview.candidate_name}"


class InterviewTranscription(models.Model):
    """Transcription of the interview audio using Whisper"""

    interview = models.OneToOneField(
        TelephonicInterview,
        on_delete=models.CASCADE,
        related_name='transcription'
    )
    
    # Full transcription
    full_text = models.TextField()
    
    # Timestamped segments (JSON)
    segments = models.JSONField(default=list)
    # Format: [{"start": 0.0, "end": 5.2, "text": "Hello, how are you?", "speaker": "recruiter"}, ...]
    
    # Language detection
    detected_language = models.CharField(max_length=10, default='en')
    confidence = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        null=True,
        blank=True
    )
    
    # Processing info
    processing_status = models.CharField(
        max_length=20,
        choices=[
            ('pending', 'Pending'),
            ('processing', 'Processing'),
            ('completed', 'Completed'),
            ('failed', 'Failed'),
        ],
        default='pending'
    )
    processing_time_seconds = models.FloatField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Whisper model used
    model_used = models.CharField(max_length=50, default='whisper-1')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'interview_transcriptions'
    
    def __str__(self):
        return f"Transcription - {self.interview.candidate_name}"
    
class InterviewPerformanceResult(models.Model):
    """AI-analyzed performance results"""

    interview = models.OneToOneField(
        TelephonicInterview,
        on_delete=models.CASCADE,
        related_name='performance_result'
    )
    
    # Overall score
    overall_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Individual metric scores
    communication_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    technical_knowledge_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    problem_solving_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    enthusiasm_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    clarity_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    professionalism_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Decision
    decision = models.CharField(
        max_length=20,
        choices=[
            ('qualified', 'Qualified'),
            ('not_qualified', 'Not Qualified'),
            ('pending', 'Pending Review'),
        ],
        default='pending'
    )
    
    # AI Analysis
    ai_summary = models.TextField(blank=True, null=True)
    key_highlights = models.JSONField(default=list)
    areas_for_improvement = models.JSONField(default=list)
    technical_assessment = models.TextField(blank=True, null=True)
    communication_assessment = models.TextField(blank=True, null=True)
    
    # Extracted insights from transcription
    key_topics_discussed = models.JSONField(default=list)
    questions_asked_count = models.IntegerField(default=0)
    candidate_response_quality = models.CharField(max_length=20, blank=True, null=True)
    
    # Manual override
    manual_score_override = models.IntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    manual_decision_override = models.CharField(
        max_length=20,
        choices=[
            ('qualified', 'Qualified'),
            ('not_qualified', 'Not Qualified'),
        ],
        blank=True,
        null=True
    )
    override_reason = models.TextField(blank=True, null=True)
    overridden_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='overridden_interviews'
    )
    overridden_at = models.DateTimeField(null=True, blank=True)
    
    # Processing metadata
    processing_time_seconds = models.FloatField(null=True, blank=True)
    ai_model_used = models.CharField(max_length=100, default='gemini-pro')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'interview_performance_results'
    
    def __str__(self):
        return f"Performance - {self.interview.candidate_name} - {self.overall_score}/100"
    
    @property
    def final_score(self):
        """Return manual override score if exists, else AI score"""
        return self.manual_score_override if self.manual_score_override is not None else self.overall_score
    
    @property
    def final_decision(self):
        """Return manual override decision if exists, else AI decision"""
        return self.manual_decision_override if self.manual_decision_override else self.decision


class InterviewFeedback(models.Model):
    """
    Optional manual feedback from interviewer
    """
    interview = models.OneToOneField(
        TelephonicInterview,
        on_delete=models.CASCADE,
        related_name='manual_feedback'
    )
    
    provided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='interview_feedbacks'
    )
    
    # Rating
    overall_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    # Detailed feedback
    strengths = models.TextField()
    weaknesses = models.TextField()
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('strong_yes', 'Strong Yes'),
            ('yes', 'Yes'),
            ('maybe', 'Maybe'),
            ('no', 'No'),
            ('strong_no', 'Strong No'),
        ]
    )
    
    comments = models.TextField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'interview_feedbacks'
    
    def __str__(self):
        return f"Feedback - {self.interview.candidate_name} by {self.provided_by.full_name}"