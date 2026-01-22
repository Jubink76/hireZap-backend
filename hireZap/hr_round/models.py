from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from job.models import JobModel
from application.models import ApplicationModel
from selection_process.models import SelectionStageModel


class HRRoundSettings(models.Model):

    job = models.OneToOneField(
        JobModel,
        on_delete=models.CASCADE,
        related_name='hr_settings'
    )
    default_duration_minutes = models.IntegerField(default=45)
    auto_schedule_enabled = models.BooleanField(default=False)
    send_reminders = models.BooleanField(default=True)
    reminder_hours_before = models.IntegerField(default=24)

    enable_recording = models.BooleanField(default=True)
    enable_chat = models.BooleanField(default=True)

    communication_weight = models.IntegerField(default=25)
    culture_fit_weight = models.IntegerField(default=20)
    motivation_weight = models.IntegerField(default=15)
    professionalism_weight = models.IntegerField(default=15)
    problem_solving_weight = models.IntegerField(default=15)
    team_collaboration_weight = models.IntegerField(default=10)
    
    # Qualification Threshold
    minimum_qualifying_score = models.IntegerField(
        default=70,
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_round_settings'
    
    def __str__(self):
        return f"HR Settings - {self.job.job_title}"
    
class HRInterview(models.Model):
    """Main HR Interview record"""
    
    STATUS_CHOICES = [
        ('not_scheduled', 'Not Scheduled'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('candidate_joined', 'Candidate Joined'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]
    
    application = models.OneToOneField(
        ApplicationModel,
        on_delete=models.CASCADE,
        related_name='hr_interview'
    )
    job = models.ForeignKey(
        JobModel,
        on_delete=models.CASCADE,
        related_name='hr_interviews'
    )
    stage = models.ForeignKey(
        SelectionStageModel,
        on_delete=models.CASCADE,
        related_name='hr_interviews',
        null=True,
        blank=True
    )

    scheduled_at = models.DateTimeField(null=True, blank=True, db_index=True)
    scheduled_duration_minutes = models.IntegerField(default=45)
    timezone = models.CharField(max_length=100, default='Asia/Kolkata')
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_scheduled',
        db_index=True
    )


    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    candidate_joined_at = models.DateTimeField(null=True, blank=True)
    actual_duration_minutes = models.IntegerField(null=True, blank=True)
    
    # Participants
    conducted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conducted_hr_interviews'
    )
    
    # Notes
    scheduling_notes = models.TextField(blank=True, null=True)
    cancellation_reason = models.TextField(blank=True, null=True)
    
    # Notifications
    notification_sent = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    reminder_sent = models.BooleanField(default=False)
    
    # Meeting Link (for reference)
    meeting_link = models.CharField(max_length=500, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_interviews'
        ordering = ['scheduled_at']
        indexes = [
            models.Index(fields=['job', 'status']),
            models.Index(fields=['application', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['status', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"HR Interview - {self.application.first_name} {self.application.last_name} - {self.status}"
    
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
    

class MeetingSession(models.Model):
    """WebRTC video meeting session tracking"""
    
    interview = models.OneToOneField(
        HRInterview,
        on_delete=models.CASCADE,
        related_name='meeting_session'
    )
    
    # Session identifiers
    session_id = models.CharField(max_length=100, unique=True, db_index=True)
    room_id = models.CharField(max_length=100, db_index=True)
    
    # Participants
    recruiter_id = models.CharField(max_length=100)
    candidate_id = models.CharField(max_length=100)
    
    # Connection Status
    recruiter_connected = models.BooleanField(default=False)
    candidate_connected = models.BooleanField(default=False)
    
    # Recording Status
    is_recording = models.BooleanField(default=False)
    recording_started_at = models.DateTimeField(null=True, blank=True)
    recording_stopped_at = models.DateTimeField(null=True, blank=True)
    
    # Connection Quality
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
    
    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    recruiter_joined_at = models.DateTimeField(null=True, blank=True)
    candidate_joined_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_meeting_sessions'
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['room_id']),
            models.Index(fields=['interview']),
        ]
    
    def __str__(self):
        return f"Meeting Session {self.session_id} - {self.interview.candidate_name}"


class InterviewRecording(models.Model):
    """Video recording metadata"""
    
    PROCESSING_STATUS_CHOICES = [
        ('pending', 'Pending Upload'),
        ('uploading', 'Uploading'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    interview = models.OneToOneField(
        HRInterview,
        on_delete=models.CASCADE,
        related_name='recording'
    )
    
    # Recording Files
    video_url = models.URLField(max_length=1024, blank=True, null=True)
    video_key = models.CharField(max_length=500, blank=True, null=True)
    thumbnail_url = models.URLField(max_length=1024, blank=True, null=True)
    thumbnail_key = models.CharField(max_length=500, blank=True, null=True)
    
    # Recording Metadata
    duration_seconds = models.IntegerField(null=True, blank=True)
    file_size_bytes = models.BigIntegerField(null=True, blank=True)
    video_format = models.CharField(max_length=20, default='webm')
    resolution = models.CharField(max_length=20, blank=True, null=True)  # e.g., "1280x720"
    
    # Processing Status
    processing_status = models.CharField(
        max_length=20,
        choices=PROCESSING_STATUS_CHOICES,
        default='pending'
    )
    processing_error = models.TextField(blank=True, null=True)
    
    # Upload Timestamps
    upload_started_at = models.DateTimeField(null=True, blank=True)
    upload_completed_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_interview_recordings'
    
    def __str__(self):
        return f"Recording - {self.interview.candidate_name}"


class InterviewNotes(models.Model):
    """Recruiter notes with structured sections and ratings"""
    
    interview = models.OneToOneField(
        HRInterview,
        on_delete=models.CASCADE,
        related_name='notes'
    )
    
    recorded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hr_interview_notes'
    )
    
    # Section 1: Communication (out of 100)
    communication_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    communication_notes = models.TextField(blank=True, null=True)
    
    # Section 2: Culture Fit (out of 100)
    culture_fit_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    culture_fit_notes = models.TextField(blank=True, null=True)
    
    # Section 3: Motivation (out of 100)
    motivation_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    motivation_notes = models.TextField(blank=True, null=True)
    
    # Section 4: Professionalism (out of 100)
    professionalism_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    professionalism_notes = models.TextField(blank=True, null=True)
    
    # Section 5: Problem Solving (out of 100)
    problem_solving_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    problem_solving_notes = models.TextField(blank=True, null=True)
    
    # Section 6: Team Collaboration (out of 100)
    team_collaboration_rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    team_collaboration_notes = models.TextField(blank=True, null=True)
    
    # Overall Assessment
    overall_impression = models.TextField(blank=True, null=True)
    strengths = models.TextField(blank=True, null=True)
    areas_for_improvement = models.TextField(blank=True, null=True)
    
    # Additional Notes
    general_notes = models.TextField(blank=True, null=True)
    
    # Calculated Score (weighted average)
    calculated_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        null=True,
        blank=True
    )
    
    # Final Decision
    recommendation = models.CharField(
        max_length=20,
        choices=[
            ('strong_yes', 'Strong Yes - Hire'),
            ('yes', 'Yes - Hire'),
            ('maybe', 'Maybe - Need Discussion'),
            ('no', 'No - Reject'),
            ('strong_no', 'Strong No - Reject'),
        ],
        null=True,
        blank=True
    )
    
    # Flags
    is_finalized = models.BooleanField(default=False)
    finalized_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_interview_notes'
    
    def __str__(self):
        return f"Notes - {self.interview.candidate_name}"
    
    def calculate_weighted_score(self):
        """Calculate weighted score based on settings"""
        try:
            settings = self.interview.job.hr_settings
        except:
            # Use default weights if settings not found
            settings = None
        
        # Get weights (defaults if no settings)
        weights = {
            'communication': getattr(settings, 'communication_weight', 25) if settings else 25,
            'culture_fit': getattr(settings, 'culture_fit_weight', 20) if settings else 20,
            'motivation': getattr(settings, 'motivation_weight', 15) if settings else 15,
            'professionalism': getattr(settings, 'professionalism_weight', 15) if settings else 15,
            'problem_solving': getattr(settings, 'problem_solving_weight', 15) if settings else 15,
            'team_collaboration': getattr(settings, 'team_collaboration_weight', 10) if settings else 10,
        }
        
        # Calculate weighted score
        total_score = 0
        total_weight = 0
        
        if self.communication_rating is not None:
            total_score += self.communication_rating * (weights['communication'] / 100)
            total_weight += weights['communication']
        
        if self.culture_fit_rating is not None:
            total_score += self.culture_fit_rating * (weights['culture_fit'] / 100)
            total_weight += weights['culture_fit']
        
        if self.motivation_rating is not None:
            total_score += self.motivation_rating * (weights['motivation'] / 100)
            total_weight += weights['motivation']
        
        if self.professionalism_rating is not None:
            total_score += self.professionalism_rating * (weights['professionalism'] / 100)
            total_weight += weights['professionalism']
        
        if self.problem_solving_rating is not None:
            total_score += self.problem_solving_rating * (weights['problem_solving'] / 100)
            total_weight += weights['problem_solving']
        
        if self.team_collaboration_rating is not None:
            total_score += self.team_collaboration_rating * (weights['team_collaboration'] / 100)
            total_weight += weights['team_collaboration']
        
        # Return weighted average if any ratings exist
        if total_weight > 0:
            return round(total_score)
        
        return None


class InterviewChatMessage(models.Model):
    """Chat messages during interview (stored temporarily in DB, cached in Redis)"""
    
    interview = models.ForeignKey(
        HRInterview,
        on_delete=models.CASCADE,
        related_name='chat_messages'
    )
    
    sender_id = models.CharField(max_length=100)  # User ID
    sender_type = models.CharField(
        max_length=20,
        choices=[
            ('recruiter', 'Recruiter'),
            ('candidate', 'Candidate'),
        ]
    )
    
    message = models.TextField()
    
    # Message Metadata
    is_system_message = models.BooleanField(default=False)
    read_by_recipient = models.BooleanField(default=False)
    
    sent_at = models.DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        db_table = 'hr_interview_chat_messages'
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['interview', 'sent_at']),
        ]
    
    def __str__(self):
        return f"Chat - {self.sender_type} - {self.sent_at}"


class InterviewResult(models.Model):
    """Final interview result and decision"""
    
    interview = models.OneToOneField(
        HRInterview,
        on_delete=models.CASCADE,
        related_name='result'
    )
    
    # Final Score (from notes)
    final_score = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    
    # Decision
    decision = models.CharField(
        max_length=20,
        choices=[
            ('qualified', 'Qualified'),
            ('not_qualified', 'Not Qualified'),
            ('pending_review', 'Pending Review'),
        ],
        default='pending_review'
    )
    
    # Decision Details
    decision_reason = models.TextField(blank=True, null=True)
    next_steps = models.TextField(blank=True, null=True)
    
    # Decision Made By
    decided_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='hr_interview_decisions'
    )
    decided_at = models.DateTimeField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'hr_interview_results'
    
    def __str__(self):
        return f"Result - {self.interview.candidate_name} - {self.decision}"